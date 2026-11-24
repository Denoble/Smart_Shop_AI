
from pydantic import BaseModel, Field


class AspectInsight(BaseModel):
    sentiment: float = 0.0
    mentions: int = 0


class ReviewInsight(BaseModel):
    product_id: str

    review_count: int = 0

    positive_ratio: float = 0.0
    negative_ratio: float = 0.0
    neutral_ratio: float = 0.0

    sentiment_score: float = 0.0
    confidence: float = 0.0

    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)

    aspects: dict[str, AspectInsight] = Field(
        default_factory=dict
    )
