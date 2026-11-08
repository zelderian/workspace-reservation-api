import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")

INTERNAL_ERROR_MESSAGE = "Внутрішня помилка сервера. Спробуйте пізніше."


async def unhandled_exception_handler(request: Request, exc: Exception):
    error_id = uuid.uuid4().hex[:12]
    logger.exception(
        "Unhandled error %s on %s %s", error_id, request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"detail": INTERNAL_ERROR_MESSAGE, "error_id": error_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, unhandled_exception_handler)
