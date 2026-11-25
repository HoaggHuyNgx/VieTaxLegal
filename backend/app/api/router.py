from fastapi import APIRouter

from app.api.routes import admin, auth, auth_email, auth_google, chat, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(auth_email.router)
api_router.include_router(auth_google.router)
api_router.include_router(admin.router)
api_router.include_router(chat.router)
