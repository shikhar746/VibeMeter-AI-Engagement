import logging
import os
import pandas as pd
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ENGAGEMENT_CSV_PATH
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


app = FastAPI(title="Deloitte VibeMeter API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)