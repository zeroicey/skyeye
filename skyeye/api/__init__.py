"""API package"""
from .videos import router as videos_router
from .search import router as search_router
from .persons import router as persons_router

__all__ = ["videos_router", "search_router", "persons_router"]
