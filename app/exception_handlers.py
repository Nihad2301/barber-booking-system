from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.auth.exceptions import AppException


def _safe_errors(exc: RequestValidationError):
    """Proactively stringify ctx values to prevent serialization errors"""
    safe = []
    for e in exc.errors():
        item = {
            "type": e.get("type"),
            "loc": e.get("loc"),
            "msg": e.get("msg")
        }
        if "ctx" in e:
            item["ctx"] = {k: str(v) for k, v in e["ctx"].items()}
        safe.append(item)
    return safe


async def custom_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handler for custom AppException subclasses"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "status_code": exc.status_code,
                "message": exc.message,
                "path": request.url.path,
                "method": request.method
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for Pydantic RequestValidationError (list of field errors)"""
    method = getattr(request, "method", None)
    url = getattr(request, "url", None)
    path = getattr(url, "path", None)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "status_code": 422,
                "message": "Validation error",
                "details": _safe_errors(exc=exc),
                "path": path,
                "method": method
            }
        }
    )
