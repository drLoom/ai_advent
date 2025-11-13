from pydantic import BaseModel


class Review(BaseModel):
    sentiment: str
    positive_feedback: list[str]
    issues: list[str]
    rating: int
