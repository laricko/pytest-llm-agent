import os
import sqlite3
from datetime import datetime

from pytest_llm_agent.core.dtos import UnitTest
from pytest_llm_agent.core.protocols import (
    DEFAULT_DB_PATH,
    UnitTestDbRepositoryProtocol,
)


def _dt_to_str(dt: datetime) -> str:
    return dt.isoformat()


def _str_to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _row_to_unit_test(row: sqlite3.Row) -> UnitTest:
    return UnitTest(
        id=row["id"],
        target=row["target"],
        test=row["test"],
        description=row["description"],
        created_at=_str_to_dt(row["created_at"]),
    )


class SqliteUnitTestDbRepository(UnitTestDbRepositoryProtocol):
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self._db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        # recommended sqlite settings
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _ensure_schema(self) -> None:
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS unit_tests (
                    id TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    test TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_unit_tests_target ON unit_tests(target)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_unit_tests_test ON unit_tests(test)")
            conn.commit()

    def create(self, unit_test: UnitTest) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO unit_tests (id, target, test, description, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    unit_test.id,
                    unit_test.target,
                    unit_test.test,
                    unit_test.description,
                    _dt_to_str(unit_test.created_at),
                ),
            )
            conn.commit()

    def get_by_id(self, id: str) -> UnitTest | None:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM unit_tests WHERE id = ?", (id,))
            row = cur.fetchone()
            return _row_to_unit_test(row) if row else None

    def update_unit_test(self, unit_test: UnitTest) -> UnitTest:
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE unit_tests
                SET target = ?, test = ?, description = ?
                WHERE id = ?
                """,
                (unit_test.target, unit_test.test, unit_test.description, unit_test.id),
            )
            if cur.rowcount == 0:
                raise KeyError(f"UnitTest not found: {unit_test.id}")
            conn.commit()
        return unit_test

    def delete_unit_test(self, id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM unit_tests WHERE id = ?", (id,))
            conn.commit()

    def bulk_register_unit_tests(self, unit_tests: list[UnitTest]):
        if not unit_tests:
            return

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO unit_tests (id, target, test, description, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        ut.id,
                        ut.target,
                        ut.test,
                        ut.description,
                        _dt_to_str(ut.created_at),
                    )
                    for ut in unit_tests
                ],
            )
            conn.commit()

    def get_by_target(self, target: str) -> list[UnitTest]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM unit_tests WHERE target = ? ORDER BY created_at",
                (target,),
            )
            return [_row_to_unit_test(r) for r in cur.fetchall()]

    def get_by_target_file(self, target_file: str) -> list[UnitTest]:
        prefix = f"{target_file}::"
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM unit_tests WHERE target LIKE ? ORDER BY created_at",
                (prefix + "%",),
            )
            return [_row_to_unit_test(r) for r in cur.fetchall()]

    def get_by_test_file(self, test_file: str) -> list[UnitTest]:
        prefix = f"{test_file}::"
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM unit_tests WHERE test LIKE ? ORDER BY created_at",
                (prefix + "%",),
            )
            return [_row_to_unit_test(r) for r in cur.fetchall()]
