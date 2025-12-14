
from datetime import datetime

from pydantic import BaseModel, Field


class UnitTestIn(BaseModel):

    target: str = Field(
        ...,
        description="The target function or method for the unit test.",
        examples=["src/foo.py::create_user", "src/bar.py::BarClass.method"],
    )
    test: str = Field(
        ...,
        description="The file path of the unit test.",
        examples=["tests/test_foo.py::test__create__user__success"],
    )
    description: str = Field(
        ...,
        description="A brief description of what the unit test is verifying.",
        examples=["Successful tests the creation of a new user."],
    )


class UnitTest(UnitTestIn):
    id: str = Field(
        ...,
        description="A unique identifier for the unit test.",
        examples=["test_foo_create_user_success_123"],
    )
    created_at: datetime = Field(default_factory=datetime.now)
