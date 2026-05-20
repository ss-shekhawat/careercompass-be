import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1 import auth, profile
from app.core.config import settings
from app.db.session import engine


API_V1_PREFIX = "/api/v1"

logger = logging.getLogger("careercompass")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection OK")
    except Exception as e:
        logger.error("Database connection FAILED at startup: %s", e)
    yield


app = FastAPI(
    title="CareerCompass API",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

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


app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(profile.router, prefix=API_V1_PREFIX)