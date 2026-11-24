# ai/agents/recommendation.py

from pydantic import BaseModel
import os
import sys
from pathlib import Path


from smartShopAi.models. pydantic_models import Product, Review
from smartShopAi.database.embedding_model import *
from smartShopAi.database. embedding_query import *
from smartShopAi.read_env_variables. read_env_variable_file import get_openai_api_key






class Recommendation(BaseModel):
    product_id: str
    reason: str
    score: float


class RecommendationResponse(BaseModel):
    recommendations: list[Recommendation]


class RecommendationAgent:

    def recommend(
        self,
        products: list[ProductResult],
        user_preferences: dict | None = None,
        limit: int = 5
    ) -> RecommendationResponse:

        user_preferences = user_preferences or {}

        results = []

        for product in products:

            score = product.final_score

            # Lightweight personalization layer
            preferred_brands = user_preferences.get(
                "preferred_brands", []
            )

            if product.brand.lower() in {
                b.lower() for b in preferred_brands
            }:
                score += 0.10

            results.append(
                Recommendation(
                    product_id=product.product_id,
                    reason=self._reason(product),
                    score=min(score, 1.0)
                )
            )

        results.sort(
            key=lambda x: x.score,
            reverse=True
        )

        return RecommendationResponse(
            recommendations=results[:limit]
        )

    @staticmethod
    def _reason(product: ProductResult) -> str:

        reasons = []

        if product.semantic_score >= 0.80:
            reasons.append("strong match")

        if product.rating >= 4.5:
            reasons.append("high customer rating")

        if product.price_score >= 0.50:
            reasons.append("good price")

        if not reasons:
            reasons.append("matches your search")

        return ", ".join(reasons)
