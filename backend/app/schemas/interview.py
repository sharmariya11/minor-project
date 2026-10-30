from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class InterviewSessionCreate(BaseModel):
    user_id: Optional[int] = 1
    job_role_id: Optional[int] = None
    job_role: Optional[str] = None


class InterviewSessionResponse(BaseModel):
    id: int
    user_id: int
    job_role_id: int
    started_at: datetime | None = None
    status: str

    class Config:
        from_attributes = True
