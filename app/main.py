from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import compare, health
from app.core.logging import configure_logging
from app.core.security import limiter
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    init_db()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="AI Career Coach",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health.router)
    application.include_router(compare.router)
    return application


app = create_app()
