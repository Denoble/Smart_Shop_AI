# ai/reviews/agent.py

import os

from pydantic import BaseModel, Field
from openai import OpenAI

from src.smartShopAi.reviews.models import (
    AspectInsight,
    ReviewInsight,
)


class ReviewAnalysis(BaseModel):
    pros: list[str] = []
    cons: list[str] = []
    aspects: dict[str, AspectInsight] = {}


class ReviewIntelligenceAgent:

    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"]
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-4.1-mini"
        )

    def analyze(
        self,
        product_id: str,
        reviews: list[str],
        statistics: dict,
    ) -> ReviewInsight:

        if not reviews:
            return ReviewInsight(
                product_id=product_id,
                **statistics
            )

        review_text = "\n".join(
            f"- {review}"
            for review in reviews
        )

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": """
You are the SmartShop Review Intelligence Agent.

Analyze customer reviews.

Extract:
- recurring pros
- recurring cons
- important product aspects
- sentiment for each aspect
- number of mentions for each aspect

Do not invent information.

Return only the requested structured output.
"""
                },
                {
                    "role": "user",
                    "content": review_text
                }
            ],
            text_format=ReviewAnalysis
        )

        analysis = response.output_parsed

        return ReviewInsight(
            product_id=product_id,
            **statistics,
            pros=analysis.pros,
            cons=analysis.cons,
            aspects=analysis.aspects,
        )
