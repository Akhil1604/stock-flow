import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import catalog, orders, system
from app.config import get_settings
from app.domain.errors import (
    DomainError,
    InsufficientInventory,
    InvalidOrder,
    OrderAlreadyCancelled,
    OrderNotFound,
    ProductNotFound,
)
from app.infrastructure.db import SessionLocal, init_db
from app.infrastructure.messaging import KafkaEventPublisher, publish_pending_events
from app.infrastructure.observability import configure_logging, metrics_middleware

logger = logging.getLogger(__name__)


async def _outbox_loop(stop_event: asyncio.Event) -> None:
    publisher = KafkaEventPublisher()
    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                published = publish_pending_events(publisher, db)
                if published:
                    logger.info("Published %s outbox events", published)
            finally:
                db.close()
        except Exception:
            logger.exception("Outbox publisher cycle failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=2.0)
        except TimeoutError:
            pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    stop_event = asyncio.Event()
    task = asyncio.create_task(_outbox_loop(stop_event)) if settings.outbox_enabled else None
    yield
    if task:
        stop_event.set()
        await task


app = FastAPI(
    title="StockFlow API",
    version="1.0.0",
    description="Reliable inventory reservation and order orchestration API.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(metrics_middleware)
app.include_router(system.router, prefix="/api/v1")
app.include_router(catalog.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")


@app.exception_handler(ProductNotFound)
@app.exception_handler(OrderNotFound)
def handle_not_found(_: Request, exc: DomainError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InsufficientInventory)
def handle_conflict(_: Request, exc: DomainError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(OrderAlreadyCancelled)
def handle_cancelled(_: Request, exc: DomainError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(InvalidOrder)
def handle_bad_order(_: Request, exc: DomainError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(ValueError)
def handle_value_error(_: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})
