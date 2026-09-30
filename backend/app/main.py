import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, interactions, movies, recommendations
from app.core.config import get_settings
from app.db.database import Base, engine

settings = get_settings()
logging.basicConfig(level=settings.app_log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env == "development" and settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)
    logging.getLogger(__name__).info("CineMatch API started")
    yield

app = FastAPI(title="CineMatch API", version="0.1.0", docs_url="/docs", openapi_url="/openapi.json", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(movies.router, prefix=settings.api_prefix)
app.include_router(interactions.ratings_router, prefix=settings.api_prefix)
app.include_router(interactions.watchlist_router, prefix=settings.api_prefix)
app.include_router(interactions.history_router, prefix=settings.api_prefix)
app.include_router(interactions.users_router, prefix=settings.api_prefix)
app.include_router(recommendations.router, prefix=settings.api_prefix)

@app.get("/api/health", tags=["health"])
def health(): return {"status": "ok"}
