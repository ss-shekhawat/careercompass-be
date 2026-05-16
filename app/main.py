from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="CareerCompass API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — must allow credentials because the frontend uses `credentials: "include"`.
# When allow_credentials=True, allow_origins cannot be ["*"] — must be explicit.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "careercompass-api", "env": settings.ENV, "status": "ok"}


@app.get("/health")
def health():
    """Lightweight liveness check. Render pings this; also used to wake the
    free-tier dyno before demos."""
    return {"status": "ok"}


# Day 2 will mount: app.include_router(auth_router, prefix="/api/v1/auth")
