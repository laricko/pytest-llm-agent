import hashlib
import re
from datetime import datetime
from pathlib import Path

from pytest_llm_agent.core import dtos
from pytest_llm_agent.core.protocols import UnitTestDbRepositoryProtocol

_BLOCK_BEGIN = "# === PYTEST_LLM_AGENT:BEGIN id={id} ==="
_BLOCK_END = "# === PYTEST_LLM_AGENT:END id={id} ==="


def _split_test_selector(test: str) -> tuple[str, str | None]:
    if "::" not in test:
        return test, None
    file_path, selector = test.split("::", 1)
    return file_path, selector or None


def _ensure_parent_dirs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _render_block(unit_test_id: str, content: str) -> str:
    content = content.rstrip() + "\n"
    return (
        _BLOCK_BEGIN.format(id=unit_test_id) + "\n"
        + content +
        _BLOCK_END.format(id=unit_test_id) + "\n"
    )


def _replace_or_append_block(file_text: str, unit_test_id: str, new_block: str) -> str:
    begin = re.escape(_BLOCK_BEGIN.format(id=unit_test_id))
    end = re.escape(_BLOCK_END.format(id=unit_test_id))
    pattern = re.compile(rf"^{begin}\n.*?^{end}\n?", re.MULTILINE | re.DOTALL)

    if pattern.search(file_text):
        return pattern.sub(new_block, file_text, count=1)

    if file_text and not file_text.endswith("\n"):
        file_text += "\n"
    if file_text and not file_text.endswith("\n\n"):
        file_text += "\n"
    return file_text + new_block


def _remove_block(file_text: str, unit_test_id: str) -> str:
    begin = re.escape(_BLOCK_BEGIN.format(id=unit_test_id))
    end = re.escape(_BLOCK_END.format(id=unit_test_id))
    pattern = re.compile(rf"^{begin}\n.*?^{end}\n?", re.MULTILINE | re.DOTALL)
    return pattern.sub("", file_text).rstrip() + "\n"


def make_unit_test_id(unit_test_in: dtos.UnitTestIn) -> str:
    prefix = unit_test_in.test.split("::")[1]
    return f"{prefix}_{hashlib.sha1(unit_test_in.test.encode('utf-8')).hexdigest()[:6]}"


class PytestAgentToolsService:
    def __init__(self, unit_test_repo: UnitTestDbRepositoryProtocol):
        self._unit_test_repo = unit_test_repo

    def register_unit_test(self, unit_test: dtos.UnitTest) -> dtos.UnitTest:
        self._unit_test_repo.create(unit_test)
        return unit_test

    def get_unit_test(self, id: str) -> dtos.UnitTest | None:
        return self._unit_test_repo.get_by_id(id)

    def update_unit_test(self, unit_test: dtos.UnitTest) -> dtos.UnitTest:
        return self._unit_test_repo.update_unit_test(unit_test)

    def delete_unit_test(self, id: str) -> None:
        self._unit_test_repo.delete_unit_test(id)

    def bulk_register_unit_tests(self, unit_tests: list[dtos.UnitTest]) -> None:
        self._unit_test_repo.bulk_register_unit_tests(unit_tests)

    def get_tests_by_target(self, target: str) -> list[dtos.UnitTest]:
        return self._unit_test_repo.get_by_target(target)

    def get_tests_by_target_file(self, target_file: str) -> list[dtos.UnitTest]:
        return self._unit_test_repo.get_by_target_file(target_file)

    def get_tests_by_test_file(self, test_file: str) -> list[dtos.UnitTest]:
        return self._unit_test_repo.get_by_test_file(test_file)

    def read_test_file(self, test_file: str) -> str:
        path = Path(test_file)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def upsert_generated_test_block(
        self,
        unit_test: dtos.UnitTest,
        content: str,
    ) -> None:
        test_file, _ = _split_test_selector(unit_test.test)
        path = Path(test_file)
        _ensure_parent_dirs(path)

        file_text = path.read_text(encoding="utf-8") if path.exists() else ""
        new_block = _render_block(unit_test.id, content)
        updated = _replace_or_append_block(file_text, unit_test.id, new_block)
        path.write_text(updated, encoding="utf-8")

    def remove_generated_test_block(self, unit_test_id: str, test_file: str) -> None:
        path = Path(test_file)
        if not path.exists():
            return
        file_text = path.read_text(encoding="utf-8")
        updated = _remove_block(file_text, unit_test_id)
        path.write_text(updated, encoding="utf-8")

    def create_test(
        self,
        unit_test_in: dtos.UnitTestIn,
        content: str,
    ) -> dtos.UnitTest:
        test = dtos.UnitTest(
            **unit_test_in.model_dump(),
            id=make_unit_test_id(unit_test_in),
        )
        self._unit_test_repo.create(test)
        self.upsert_generated_test_block(test, content)
        return test

    def update_test_content(
        self,
        unit_test_id: str,
        content: str,
    ) -> dtos.UnitTest:
        ut = self._unit_test_repo.get_by_id(unit_test_id)
        if ut is None:
            raise KeyError(f"UnitTest not found: {unit_test_id}")
        self.upsert_generated_test_block(ut, content)
        return ut

    def delete_test_everywhere(self, unit_test_id: str) -> None:
        ut = self._unit_test_repo.get_by_id(unit_test_id)
        if ut is not None:
            test_file, _ = _split_test_selector(ut.test)
            self.remove_generated_test_block(unit_test_id, test_file)
        self._unit_test_repo.delete_unit_test(unit_test_id)
