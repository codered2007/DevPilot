from typing import Literal

from pydantic import BaseModel


class ApplyCodeRequest(BaseModel):
    owner: str
    repo: str
    file_path: str
    code: str
    action: Literal[
        "fix",
        "improve",
        "refactor",
    ]