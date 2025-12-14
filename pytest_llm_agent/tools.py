from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from pytest_llm_agent.core import dtos
from pytest_llm_agent.core.services import PytestAgentToolsService


class IdInput(BaseModel):
    id: str = Field(..., description="Unit test id")


class ReadTestFileInput(BaseModel):
    test_file: str = Field(..., description="Path to test file, e.g. tests/test_foo.py")


class CreateTestInput(BaseModel):
    unit_test: dtos.UnitTestIn = Field(..., description="UnitTestIn payload")
    content: str = Field(..., description="Generated pytest code to insert/update in managed block")


class UpdateTestContentInput(BaseModel):
    unit_test_id: str = Field(..., description="Unit test id")
    content: str = Field(..., description="New pytest code for the managed block")


class RemoveGeneratedBlockInput(BaseModel):
    unit_test_id: str = Field(..., description="Unit test id")
    test_file: str = Field(..., description="Path to test file, e.g. tests/test_foo.py")


class UpsertGeneratedBlockInput(BaseModel):
    unit_test: dtos.UnitTest = Field(..., description="UnitTest payload (must contain id/test)")
    content: str = Field(..., description="Pytest code to write into the managed block")


class BulkRegisterUnitTestsInput(BaseModel):
    unit_tests: list[dtos.UnitTest] = Field(..., description="List of UnitTest records to register")


class UpdateUnitTestInput(BaseModel):
    unit_test: dtos.UnitTest = Field(..., description="Updated UnitTest record")


class GetByTargetInput(BaseModel):
    target: str = Field(..., description="Target selector, e.g. src/foo.py::create_user")


class GetByTargetFileInput(BaseModel):
    target_file: str = Field(..., description="Target file path, e.g. src/foo.py")


class GetByTestFileInput(BaseModel):
    test_file: str = Field(..., description="Test file path, e.g. tests/test_foo.py")


class RegisterUnitTestInput(BaseModel):
    unit_test: dtos.UnitTest = Field(..., description="UnitTest record to store")


def build_langchain_tools(service: PytestAgentToolsService) -> list[Any]:

    @tool("unit_test_register", args_schema=RegisterUnitTestInput)
    def unit_test_register(unit_test: dtos.UnitTest) -> dict:
        """Register a UnitTest in the SQLite registry."""
        saved = service.register_unit_test(unit_test)
        return saved.model_dump()

    @tool("unit_test_get_by_id", args_schema=IdInput)
    def unit_test_get_by_id(id: str) -> dict | None:
        """Get a UnitTest by id from the SQLite registry."""
        ut = service.get_unit_test(id)
        return ut.model_dump() if ut else None

    @tool("unit_test_update", args_schema=UpdateUnitTestInput)
    def unit_test_update(unit_test: dtos.UnitTest) -> dict:
        """Update a UnitTest record in the SQLite registry."""
        ut = service.update_unit_test(unit_test)
        return ut.model_dump()

    @tool("unit_test_delete", args_schema=IdInput)
    def unit_test_delete(id: str) -> dict:
        """Delete a UnitTest record from the SQLite registry."""
        service.delete_unit_test(id)
        return {"deleted": id}

    @tool("unit_test_bulk_register", args_schema=BulkRegisterUnitTestsInput)
    def unit_test_bulk_register(unit_tests: list[dtos.UnitTest]) -> dict:
        """Bulk register UnitTests (insert or replace) into the SQLite registry."""
        service.bulk_register_unit_tests(unit_tests)
        return {"registered": len(unit_tests)}

    @tool("unit_test_get_by_target", args_schema=GetByTargetInput)
    def unit_test_get_by_target(target: str) -> list[dict]:
        """List UnitTests by exact target selector."""
        tests = service.get_tests_by_target(target)
        return [t.model_dump() for t in tests]

    @tool("unit_test_get_by_target_file", args_schema=GetByTargetFileInput)
    def unit_test_get_by_target_file(target_file: str) -> list[dict]:
        """List UnitTests whose target starts with '<target_file>::'."""
        tests = service.get_tests_by_target_file(target_file)
        return [t.model_dump() for t in tests]

    @tool("unit_test_get_by_test_file", args_schema=GetByTestFileInput)
    def unit_test_get_by_test_file(test_file: str) -> list[dict]:
        """List UnitTests whose test starts with '<test_file>::'."""
        tests = service.get_tests_by_test_file(test_file)
        return [t.model_dump() for t in tests]

    @tool("test_file_read", args_schema=ReadTestFileInput)
    def test_file_read(test_file: str) -> str:
        """Read a pytest file content (returns empty string if missing)."""
        return service.read_test_file(test_file)

    @tool("test_block_upsert", args_schema=UpsertGeneratedBlockInput)
    def test_block_upsert(unit_test: dtos.UnitTest, content: str) -> dict:
        """Upsert the managed block for a given UnitTest.id into its test file."""
        service.upsert_generated_test_block(unit_test, content)
        return {"upserted": unit_test.id}

    @tool("test_block_remove", args_schema=RemoveGeneratedBlockInput)
    def test_block_remove(unit_test_id: str, test_file: str) -> dict:
        """Remove the managed block by id from a test file."""
        service.remove_generated_test_block(unit_test_id, test_file)
        return {"removed": unit_test_id, "file": test_file}

    @tool("test_create", args_schema=CreateTestInput)
    def test_create(unit_test: dtos.UnitTestIn, content: str) -> dict:
        """
        Create a UnitTest registry entry and upsert its managed block into the file.
        Id is generated by the service (make_unit_test_id).
        """
        ut = service.create_test(unit_test, content)
        return ut.model_dump()

    @tool("test_update_content", args_schema=UpdateTestContentInput)
    def test_update_content(unit_test_id: str, content: str) -> dict:
        """Update only the managed block content in the file for an existing UnitTest id."""
        ut = service.update_test_content(unit_test_id, content)
        return ut.model_dump()

    @tool("test_delete_everywhere", args_schema=IdInput)
    def test_delete_everywhere(id: str) -> dict:
        """Delete managed block from file (if exists) and delete registry record."""
        service.delete_test_everywhere(id)
        return {"deleted_everywhere": id}

    return [
        unit_test_register,
        unit_test_get_by_id,
        unit_test_update,
        unit_test_delete,
        unit_test_bulk_register,
        unit_test_get_by_target,
        unit_test_get_by_target_file,
        unit_test_get_by_test_file,
        test_file_read,
        test_block_upsert,
        test_block_remove,
        test_create,
        test_update_content,
        test_delete_everywhere,
    ]
