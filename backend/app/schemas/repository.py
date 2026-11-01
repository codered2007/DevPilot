from pydantic import BaseModel, Field


class RepositoryImportRequest(BaseModel):
    url: str


class RepositoryHistoryRequest(BaseModel):
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)