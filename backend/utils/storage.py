import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from utils.config import settings


def ensure_upload_dir() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_citizen_id_image(file: UploadFile) -> str:
    upload_dir = ensure_upload_dir()
    ext = Path(file.filename or "").suffix.lower()
    filename = f"{uuid4().hex}{ext}"
    dest = upload_dir / filename

    with dest.open("wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)
    return str(dest)
