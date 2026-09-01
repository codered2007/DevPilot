from pydantic import BaseModel


class ExplainRequest(BaseModel):
    owner: str
    repo: str
    file_path: str
    code: str