from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, profile
from app.core.config import settings

API_V1_PREFIX = "/api/v1"

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
    return {"status": "ok"}


# Day 2 will mount: app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(profile.router, prefix=API_V1_PREFIX)