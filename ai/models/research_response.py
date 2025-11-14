from typing import Optional
from pydantic import BaseModel


class ResearchResponse(BaseModel):
    status: str
    question: str
    notes: str
    result: Optional[str] = None
