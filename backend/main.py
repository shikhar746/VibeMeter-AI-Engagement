import logging
import os
import pandas as pd
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import ENGAGEMENT_CSV_PATH
from app.limiter import limiter
from app.database import connect_db, close_db, employees
from app.services.shap_service import parse_shap_string
from app.routes import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect DB and seed employees. Shutdown: close DB."""
    await connect_db()

    if os.path.exists(ENGAGEMENT_CSV_PATH):
        try:
            df = pd.read_csv(ENGAGEMENT_CSV_PATH)
            selected = df[df["is_selected"]]
            count = 0
            for row in selected.to_dict("records"):
                await employees.update_one(
                    {"employee_id": str(row["employee_id"])},
                    {"$set": {
                        "employee_id": str(row["employee_id"]),
                        "top_impact_features": parse_shap_string(row["shap_values"]),
                    }},
                    upsert=True,
                )
                count += 1
            logger.info("Seeded %d flagged employees into MongoDB", count)
        except Exception as e:
            logger.error("CSV seed error: %s", e)
    else:
        logger.warning("%s not found — skipping seed", ENGAGEMENT_CSV_PATH)

    yield

    await close_db()


app = FastAPI(title="VibeMeter API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ORIGINS = [
    o.strip()
    for o in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-HR-Token"],
)

app.include_router(api_router)