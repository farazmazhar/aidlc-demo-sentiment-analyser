"""Application package for very-cool-sentiment-analysis.

The public entry point of the package is the ASGI application re-exported
here, so `uvicorn app:app` resolves from the repository root without needing
to name `app.main` explicitly. (FR5.1, A2)
"""

from app.main import app

__all__ = ["app"]
