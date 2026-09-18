from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.farmer import router as farmer_router
from app.api.v1.admin import router as admin_router
from app.api.v1.orchestrator import router as orchestrator_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(farmer_router)
api_router.include_router(admin_router)
api_router.include_router(orchestrator_router)
