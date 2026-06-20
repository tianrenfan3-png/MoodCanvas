import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.routes.mood import limiter, router
from app.services.analyzer.factory import get_analyzer
from app.services.firebase import init_firebase

logger = logging.getLogger(__name__)


def _warmup_analyzer_in_background() -> None:
    settings = get_settings()
    if settings.environment == "test":
        return

    def _run() -> None:
        try:
            # Let Railway healthchecks pass before loading CLIP into memory.
            time.sleep(15)
            analyzer = get_analyzer()
            if not analyzer.is_ready():
                logger.info("Warming up mood analyzer in background...")
                analyzer.warmup()
        except Exception as e:
            logger.error("Analyzer warmup failed: %s", e)

    threading.Thread(target=_run, daemon=True).start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    init_firebase(settings)
    logger.info("API starting on port %s (analyzer=%s)", settings.port, settings.analyzer_type)
    _warmup_analyzer_in_background()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Art Therapy Mood Tracker API",
        description="AI-powered mood analysis from drawings",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()
