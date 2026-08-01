from pydantic import BaseModel


class RepositoryImportRequest(BaseModel):
    url: str