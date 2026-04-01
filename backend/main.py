from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import model  # noqa: F401

from api.auth import router as auth_router
from api.rooms import router as rooms_router
from api.tenancies import router as tenancies_router
from database import Base, engine
from utils.storage import ensure_upload_dir


def create_app() -> FastAPI:
    app = FastAPI(title="Apartment Management API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(rooms_router)
    app.include_router(tenancies_router)
    return app


app = create_app()


@app.on_event("startup")
def on_startup() -> None:
    ensure_upload_dir()
    Base.metadata.create_all(bind=engine)
