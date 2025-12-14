
from datetime import datetime

from pydantic import BaseModel, Field


class UnitTest(BaseModel):
    title: str = Field(
        ...,
        description="Unique title for the unit test.",
        examples=["test__create__user__success"]
    )
    target: str = Field(
        ...,
        description="The target function or method for the unit test.",
        examples=["src/foo.py::create_user"],
    )
    target_file: str = Field(
        ...,
        description="The file path of the target function or method.",
        examples=["src/foo.py"],
    )
    test: str = Field(
        ...,
        description="The file path of the unit test.",
        examples=["tests/test_foo.py::test__create__user__success"],
    )
    test_file: str = Field(
        ...,
        description="The file path where the unit test is located.",
        examples=["tests/test_foo.py"],
    )
    description: str = Field(
        ...,
        description="A brief description of what the unit test is verifying.",
        examples=["Successful tests the creation of a new user."],
    )
    created_at: datetime = Field(default_factory=datetime.now)
