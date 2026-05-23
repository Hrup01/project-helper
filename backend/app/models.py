from pydantic import BaseModel, Field, HttpUrl


class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl
    force: bool = False


class AnalyzeResponse(BaseModel):
    project_id: str
    status: str
    cached: bool


class Project(BaseModel):
    id: str
    repo_url: str
    repo_name: str
    branch: str | None = None
    status: str
    report: str | None = None
    error: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
