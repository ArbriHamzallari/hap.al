"""Compatibility entrypoint — delegates to FastAPI app in app.main."""

from app.main import app

__all__ = ["app"]
