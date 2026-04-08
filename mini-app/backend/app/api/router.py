from fastapi import APIRouter

from app.api.routes import health, public_routes

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(public_routes.router)
