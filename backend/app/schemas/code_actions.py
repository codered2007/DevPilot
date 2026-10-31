from typing import Literal

from pydantic import BaseModel, field_validator

from app.schemas.path_validation import validate_safe_file_path


class CodeActionRequest(BaseModel):
    owner: str
    repo: str
    file_path: str
    code: str
    action: Literal["fix", "improve", "refactor"]

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, value: str) -> str:
        return validate_safe_file_path(value)
