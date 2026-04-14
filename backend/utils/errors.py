from dataclasses import dataclass


@dataclass
class AppError(Exception):
    detail: str
    status_code: int = 400
    errors: list[dict] | None = None


class BadRequestError(AppError):
    def __init__(self, detail: str, errors: list[dict] | None = None) -> None:
        super().__init__(detail=detail, status_code=400, errors=errors)


class NotFoundError(AppError):
    def __init__(self, detail: str, errors: list[dict] | None = None) -> None:
        super().__init__(detail=detail, status_code=404, errors=errors)


class ConflictError(AppError):
    def __init__(self, detail: str, errors: list[dict] | None = None) -> None:
        super().__init__(detail=detail, status_code=409, errors=errors)


class ForbiddenError(AppError):
    def __init__(self, detail: str, errors: list[dict] | None = None) -> None:
        super().__init__(detail=detail, status_code=403, errors=errors)
