from fastapi import APIRouter
from app.api.v1.config import router as config_router
from app.api.v1.documents import router as documents_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.chat import router as chat_router
from app.api.v1.logs import router as logs_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(config_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(logs_router)

__all__ = ["api_v1_router"]
