from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check", description="Returns `{ok: true}` when the service is running and reachable.")
def health():
    return JSONResponse({"ok": True})
