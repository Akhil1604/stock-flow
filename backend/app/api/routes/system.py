from fastapi import APIRouter

from app.infrastructure.observability import metrics_response

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "stockflow-api"}


@router.get("/metrics")
def metrics():
    return metrics_response()
