from fastapi import APIRouter

from src.api.auth.routes import router as auth_router
from src.api.routes.care_goals import router as care_goals_router
from src.api.routes.care_reports import router as care_reports_router
from src.api.routes.incidents import router as incidents_router
from src.api.routes.permissions import router as permissions_router
from src.api.routes.residents import router as residents_router
from src.api.routes.users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(residents_router)
api_router.include_router(care_reports_router)
api_router.include_router(care_goals_router)
api_router.include_router(incidents_router)
api_router.include_router(permissions_router)

__all__ = ["api_router"]
