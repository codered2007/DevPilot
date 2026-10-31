import re
from typing import Literal

from pydantic import BaseModel, field_validator

from app.schemas.path_validation import validate_safe_file_path


class ApplyCodeRequest(BaseModel):
    owner: str
    repo: str
    file_path: str
    code: str
    action: Literal["fix", "improve", "refactor"]

    @field_validator("owner", "repo")
    @classmethod
    def validate_repository_parts(cls, value: str) -> str:
        value = value.strip()

        if not value or value in {".", ".."}:
            raise ValueError("Owner and repository must not be empty.")

        if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
            raise ValueError("Invalid owner or repository name.")

        return value

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, value: str) -> str:
        return validate_safe_file_path(value)
