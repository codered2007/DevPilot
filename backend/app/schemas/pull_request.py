from pydantic import BaseModel


class CreatePullRequestRequest(BaseModel):
    owner: str
    repo: str
    title: str
    body: str
    head: str
    base: str = "main"