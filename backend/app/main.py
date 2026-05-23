from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.analyzer import analyze_repository, get_project, upsert_project
from app.chat import sse, stream_answer
from app.database import init_db
from app.models import AnalyzeRequest, AnalyzeResponse, ChatRequest, Project
from app.utils import normalize_repo_url, project_id_for_url


app = FastAPI(title="Project Helper API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def create_analysis(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        normalized = normalize_repo_url(str(payload.repo_url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    project_id = project_id_for_url(normalized)
    existing = get_project(project_id)
    cached = bool(existing and existing["status"] == "completed" and not payload.force)
    if not cached:
        upsert_project(normalized, "queued")
    return AnalyzeResponse(project_id=project_id, status="cached" if cached else "queued", cached=cached)


@app.get("/api/analyze/{project_id}/events")
async def analysis_events(project_id: str, repo_url: str, force: bool = False):
    async def event_stream():
        async for event in analyze_repository(repo_url, force=force):
            yield sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/projects/{project_id}", response_model=Project)
def read_project(project_id: str) -> Project:
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return Project(**project)


@app.post("/api/projects/{project_id}/chat")
async def chat(project_id: str, payload: ChatRequest):
    async def event_stream():
        async for event in stream_answer(project_id, payload.question):
            yield sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
