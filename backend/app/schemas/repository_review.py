from typing import Literal

from pydantic import BaseModel


class ReviewFinding(BaseModel):
    severity: Literal[
        "high",
        "medium",
        "low",
    ]

    title: str
    description: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None


class RepositoryReviewResponse(BaseModel):
    summary: str
    findings: list[ReviewFinding]