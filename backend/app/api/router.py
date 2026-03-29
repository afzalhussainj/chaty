from fastapi import APIRouter

from app.api.routes import auth, chat, health
from app.api.routes.admin import crawl_configs, crawl_jobs, incremental, retrieval, sources, tenants

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router)
api_router.include_router(tenants.router, prefix="/admin")
api_router.include_router(crawl_configs.router, prefix="/admin")
api_router.include_router(crawl_jobs.router, prefix="/admin")
api_router.include_router(incremental.router, prefix="/admin")
api_router.include_router(retrieval.router, prefix="/admin")
api_router.include_router(sources.router, prefix="/admin")
