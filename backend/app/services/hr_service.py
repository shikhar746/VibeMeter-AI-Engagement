import os
from typing import Optional
from fastapi import HTTPException
from app.config import HR_PASSWORD


def verify_hr_token(token: Optional[str]) -> None:
    """
    Raises 403 if the token doesn't match HR_PASSWORD env var.
    Call this at the top of any HR-only endpoint.
    """
    hr_password = os.getenv("HR_PASSWORD", HR_PASSWORD)
    if not hr_password:
        raise HTTPException(status_code=500, detail="HR_PASSWORD not configured on server.")
    if token != hr_password:
        raise HTTPException(status_code=403, detail="Forbidden — invalid HR token.")
