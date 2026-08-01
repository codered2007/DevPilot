from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.repositories import router as repository_router

app = FastAPI(
    title="DevPilot API",
    version="1.0.0",
    description="Backend API for DevPilot",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repository_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to DevPilot API 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }