from pydantic import BaseModel


class HrLoginRequest(BaseModel):
    password: str
