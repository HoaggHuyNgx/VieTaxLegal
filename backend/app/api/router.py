from fastapi import APIRouter

from app.api.routes import admin, auth, chat, email_code, google_auth, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(email_code.router)
api_router.include_router(google_auth.router)
api_router.include_router(admin.router)
api_router.include_router(chat.router)
