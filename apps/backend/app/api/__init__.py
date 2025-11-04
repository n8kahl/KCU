from fastapi import APIRouter

from . import admin, health, positions, snapshots, tickers, what_if

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(tickers.router, tags=["tickers"])
api_router.include_router(what_if.router, tags=["what-if"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(snapshots.router, tags=["snapshots"])
api_router.include_router(positions.router, tags=["positions"])
