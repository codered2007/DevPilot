from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.repositories import router as repository_router
from app.api.chat import router as chat_router
from app.api.summary import router as summary_router
from app.api.explanation import router as explanation_router
from app.api.index import router as index_router

from app.api.code_actions import router as code_actions_router
from app.api.apply_code import router as apply_code_router
from app.api.pull_request import router as pull_request_router
app = FastAPI(
    title="DevPilot API",
    version="1.0.0",
    description="Backend API for DevPilot",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(repository_router)
app.include_router(chat_router)
app.include_router(summary_router)
app.include_router(explanation_router)
app.include_router(index_router)
app.include_router(code_actions_router)
app.include_router(apply_code_router)
app.include_router(pull_request_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to DevPilot 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }