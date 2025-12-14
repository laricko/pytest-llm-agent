from typing import Protocol


class UserRepositoryProtocol(Protocol):
    def get_user_by_email(self, email: str) -> dict:
        ...

    def create_user(self, email: str) -> dict:
        ...


class UserService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def create_user(self, email: str) -> dict:
        if "@" not in email:
            raise ValueError("invalid email")

        self.user_repository.create_user(email)
        return {"email": email}
