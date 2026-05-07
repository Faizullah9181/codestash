"""Database package — re-exports from app.repositories.db for backward compatibility."""

__all__ = ["get_db", "init_db", "async_session", "Base"]


def __getattr__(name: str):
    if name in ("get_db", "init_db", "async_session"):
        from app.repositories.db import connection as _mod

        return getattr(_mod, name)
    if name == "Base":
        from app.repositories.db import models as _mod

        return getattr(_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
