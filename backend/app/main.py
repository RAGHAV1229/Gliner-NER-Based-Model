from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.config.upload_limits import (
    MULTIPART_MAX_FIELDS,
    MULTIPART_MAX_FILES,
    MULTIPART_MAX_PART_SIZE,
)
from app.database import Base, engine
from app import models  # noqa: F401
from app import batch_models  # noqa: F401
from app.routes import auth_routes, batch_routes, dashboard_routes, settings_routes
from app.services.settings_service import apply_openai_settings_to_env

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
apply_openai_settings_to_env()

_original_form = Request.form


def _unlimited_form(self, *args, **kwargs):
    kwargs.setdefault("max_files", MULTIPART_MAX_FILES)
    kwargs.setdefault("max_fields", MULTIPART_MAX_FIELDS)
    kwargs.setdefault("max_part_size", MULTIPART_MAX_PART_SIZE)
    return _original_form(self, *args, **kwargs)


Request.form = _unlimited_form

app = FastAPI(
    title="Enterprise GLiNER NER",
    description="Enterprise named-entity recognition platform with hybrid GLiNER + PII detection",
    version="2.0.0",
)

origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router)
app.include_router(batch_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(settings_routes.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "enterprise-gliner-ner"}
