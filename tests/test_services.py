from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from pytest_llm_agent.core import dtos
from pytest_llm_agent.core.services import PytestAgentToolsService, make_unit_test_id


@dataclass
class FakeUnitTestRepo:
    items: dict[str, dtos.UnitTest]

    def create(self, unit_test: dtos.UnitTest) -> None:
        if unit_test.id in self.items:
            raise KeyError(f"Already exists: {unit_test.id}")
        self.items[unit_test.id] = unit_test

    def get_by_id(self, id: str) -> dtos.UnitTest | None:
        return self.items.get(id)

    def update_unit_test(self, unit_test: dtos.UnitTest) -> dtos.UnitTest:
        if unit_test.id not in self.items:
            raise KeyError(f"Not found: {unit_test.id}")
        self.items[unit_test.id] = unit_test
        return unit_test

    def delete_unit_test(self, id: str) -> None:
        self.items.pop(id, None)

    def bulk_register_unit_tests(self, unit_tests: list[dtos.UnitTest]):
        for ut in unit_tests:
            self.items[ut.id] = ut

    def get_by_target(self, target: str) -> list[dtos.UnitTest]:
        return [ut for ut in self.items.values() if ut.target == target]

    def get_by_target_file(self, target_file: str) -> list[dtos.UnitTest]:
        prefix = f"{target_file}::"
        return [ut for ut in self.items.values() if ut.target.startswith(prefix)]

    def get_by_test_file(self, test_file: str) -> list[dtos.UnitTest]:
        prefix = f"{test_file}::"
        return [ut for ut in self.items.values() if ut.test.startswith(prefix)]


@pytest.fixture()
def repo() -> FakeUnitTestRepo:
    return FakeUnitTestRepo(items={})


@pytest.fixture()
def service(repo: FakeUnitTestRepo) -> PytestAgentToolsService:
    return PytestAgentToolsService(unit_test_repo=repo)


@pytest.fixture()
def unit_test_in(tmp_path: Path) -> dtos.UnitTestIn:
    test_file = tmp_path / "tests" / "test_example.py"
    return dtos.UnitTestIn(
        target="src/foo.py::create_user",
        test=f"{test_file}::test__create_user__success",
        description="creates a user successfully",
    )


def _test_file_path(ut_in: dtos.UnitTestIn) -> Path:
    return Path(ut_in.test.split("::", 1)[0])


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_make_unit_test_id_is_deterministic(unit_test_in: dtos.UnitTestIn):
    a = make_unit_test_id(unit_test_in)
    b = make_unit_test_id(unit_test_in)
    assert a == b


def test_make_unit_test_id_uses_test_name_prefix(unit_test_in: dtos.UnitTestIn):
    # prefix = selector name (after ::)
    selector = unit_test_in.test.split("::", 1)[1]
    uid = make_unit_test_id(unit_test_in)
    assert uid.startswith(selector + "_")
    # hash length 6 hex
    assert len(uid.split("_")[-1]) == 6


def test_create_test_creates_db_record_and_writes_block(
    service: PytestAgentToolsService,
    repo: FakeUnitTestRepo,
    unit_test_in: dtos.UnitTestIn,
):
    content = "def test_x():\n    assert 1 == 1\n"

    ut = service.create_test(unit_test_in, content)

    assert ut.id == make_unit_test_id(unit_test_in)
    assert repo.get_by_id(ut.id) is not None

    test_file_path = _test_file_path(unit_test_in)
    assert test_file_path.exists()

    text = _read(test_file_path)
    assert f"# === PYTEST_LLM_AGENT:BEGIN id={ut.id} ===" in text
    assert "def test_x():" in text
    assert f"# === PYTEST_LLM_AGENT:END id={ut.id} ===" in text


def test_create_test_creates_parent_dirs(service: PytestAgentToolsService, unit_test_in: dtos.UnitTestIn):
    test_file_path = _test_file_path(unit_test_in)
    assert not test_file_path.exists()
    assert not test_file_path.parent.exists()

    service.create_test(unit_test_in, "def test_dirs():\n    assert True\n")

    assert test_file_path.parent.exists()
    assert test_file_path.exists()


def test_upsert_replaces_existing_block_not_duplicate(
    service: PytestAgentToolsService,
    unit_test_in: dtos.UnitTestIn,
    repo: FakeUnitTestRepo,
):
    ut = dtos.UnitTest(**unit_test_in.model_dump(), id=make_unit_test_id(unit_test_in))
    repo.create(ut)

    test_file_path = _test_file_path(unit_test_in)

    service.upsert_generated_test_block(ut, "def test_a():\n    assert 1\n")
    first = _read(test_file_path)
    assert first.count(f"BEGIN id={ut.id}") == 1
    assert "def test_a()" in first

    service.upsert_generated_test_block(ut, "def test_b():\n    assert 2\n")
    second = _read(test_file_path)

    assert second.count(f"BEGIN id={ut.id}") == 1
    assert "def test_a()" not in second
    assert "def test_b()" in second


def test_read_test_file_returns_empty_for_missing_file(service: PytestAgentToolsService, tmp_path: Path):
    missing = tmp_path / "tests" / "missing.py"
    assert service.read_test_file(str(missing)) == ""


def test_read_test_file_reads_existing_file(service: PytestAgentToolsService, tmp_path: Path):
    p = tmp_path / "tests" / "test_read.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("hello\n", encoding="utf-8")

    assert service.read_test_file(str(p)) == "hello\n"


def test_remove_generated_test_block_removes_only_that_block(
    service: PytestAgentToolsService,
    unit_test_in: dtos.UnitTestIn,
    repo: FakeUnitTestRepo,
):
    test_file_path = _test_file_path(unit_test_in)

    ut1 = dtos.UnitTest(**unit_test_in.model_dump(), id="ut1")
    ut2 = dtos.UnitTest(**unit_test_in.model_dump(), id="ut2")
    repo.bulk_register_unit_tests([ut1, ut2])

    service.upsert_generated_test_block(ut1, "def test_one():\n    assert 1\n")
    service.upsert_generated_test_block(ut2, "def test_two():\n    assert 2\n")

    before = _read(test_file_path)
    assert "BEGIN id=ut1" in before
    assert "BEGIN id=ut2" in before

    service.remove_generated_test_block("ut1", str(test_file_path))

    after = _read(test_file_path)
    assert "BEGIN id=ut1" not in after
    assert "END id=ut1" not in after
    assert "BEGIN id=ut2" in after
    assert "def test_two()" in after


def test_delete_test_everywhere_removes_block_and_db_record(
    service: PytestAgentToolsService,
    repo: FakeUnitTestRepo,
    unit_test_in: dtos.UnitTestIn,
):
    ut = service.create_test(unit_test_in, "def test_del():\n    assert True\n")
    test_file_path = _test_file_path(unit_test_in)

    assert f"BEGIN id={ut.id}" in _read(test_file_path)
    assert repo.get_by_id(ut.id) is not None

    service.delete_test_everywhere(ut.id)

    assert repo.get_by_id(ut.id) is None
    assert f"BEGIN id={ut.id}" not in _read(test_file_path)


def test_update_test_content_raises_for_missing_test(service: PytestAgentToolsService):
    with pytest.raises(KeyError):
        service.update_test_content("missing_id", "def test_x():\n    assert True\n")


def test_update_test_content_updates_file_block(
    service: PytestAgentToolsService,
    repo: FakeUnitTestRepo,
    unit_test_in: dtos.UnitTestIn,
):
    ut = service.create_test(unit_test_in, "def test_old():\n    assert 1\n")
    test_file_path = _test_file_path(unit_test_in)

    service.update_test_content(ut.id, "def test_new():\n    assert 2\n")

    text = _read(test_file_path)
    assert "def test_old()" not in text
    assert "def test_new()" in text
    assert text.count(f"BEGIN id={ut.id}") == 1
