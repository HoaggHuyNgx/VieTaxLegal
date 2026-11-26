from collections.abc import Mapping

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: Mapping[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = dict(fields or {})


def app_error_handler(_: Request, error: AppError) -> JSONResponse:
    payload: dict[str, object] = {"code": error.code, "message": error.message}
    if error.fields:
        payload["fields"] = error.fields
    return JSONResponse(status_code=error.status_code, content={"error": payload})


# Errors raised by the router itself, before any of our code runs.
HTTP_ERRORS = {
    404: ("NOT_FOUND", "Không tìm thấy tài nguyên."),
    405: ("METHOD_NOT_ALLOWED", "Phương thức không được hỗ trợ."),
}


def http_error_handler(_: Request, error: HTTPException) -> JSONResponse:
    code, message = HTTP_ERRORS.get(error.status_code, ("REQUEST_FAILED", "Yêu cầu không hợp lệ."))
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": code, "message": message}},
        headers=error.headers,
    )


def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
    fields: dict[str, str] = {}
    for item in error.errors():
        location = item.get("loc", [])
        field = str(location[-1]) if location else "form"
        fields.setdefault(field, item["msg"])

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Dữ liệu gửi lên chưa hợp lệ.",
                "fields": fields,
            }
        },
    )
