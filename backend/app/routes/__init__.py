from fastapi import APIRouter
from app.routes.outreach import router as outreach_router
from app.routes.chat import router as chat_router
from app.routes.report import router as report_router
from app.routes.hr import router as hr_router

api_router = APIRouter()
api_router.include_router(outreach_router)
api_router.include_router(chat_router)
api_router.include_router(report_router)
api_router.include_router(hr_router)
