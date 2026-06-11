"""API dependencies for shared demo state."""

from app.repositories.demo_repository import DemoRepository


_demo_repository = DemoRepository()


def get_demo_repository() -> DemoRepository:
    """Return the shared in-memory demo repository."""
    return _demo_repository


def reset_demo_repository() -> DemoRepository:
    """Reset shared demo repository state for tests."""
    global _demo_repository
    _demo_repository = DemoRepository()
    return _demo_repository
