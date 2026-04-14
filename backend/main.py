from fastapi import FastAPI
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.auth import router as auth_router
from api.billing import router as billing_router
from api.resident import router as resident_router
from api.reports import router as reports_router
from api.receipts import router as receipts_router
from api.rooms import router as rooms_router
from api.tenancies import router as tenancies_router
from database import Base, engine
from utils.storage import ensure_upload_dir
from utils.errors import AppError


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_upload_dir()
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Apartment Management API", lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    def validation_exception_handler(_, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            loc = ".".join(str(item) for item in err.get("loc", []))
            errors.append(
                {
                    "loc": loc,
                    "msg": err.get("msg"),
                    "type": err.get("type"),
                }
            )
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": errors,
            },
        )

    @app.exception_handler(AppError)
    def app_error_handler(_, exc: AppError):
        content = {"detail": exc.detail}
        if exc.errors:
            content["errors"] = exc.errors
        return JSONResponse(status_code=exc.status_code, content=content)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(billing_router)
    app.include_router(resident_router)
    app.include_router(reports_router)
    app.include_router(receipts_router)
    app.include_router(rooms_router)
    app.include_router(tenancies_router)
    return app


app = create_app()
