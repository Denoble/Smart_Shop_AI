from psycopg import Connection
import pandas as pd
import numpy as np

import psycopg
from pgvector.psycopg import register_vector

from smartShopAi.models. pydantic_models import *
from smartShopAi.database. embedding_query import *
from smartShopAi.database. embedding_model import *
from smartShopAi.database.query_parser import *
from smartShopAi.models.pydantic_models import ProductFilters

def calculate_rating_score(rating: float) -> float:
    """
    Normalize a 1-5 rating to 0-1.
    """
    return max(0.0, min(rating / 5.0, 1.0))


def calculate_price_score(
    price: float,
    intent: SearchIntent
) -> float:
    """
    Higher score for products further below the maximum budget.
    """
    if intent.max_price is None:
        return 0.5

    if price > intent.max_price:
        return 0.0

    if intent.max_price == 0:
        return 1.0 if price == 0 else 0.0

    return max(
        0.0,
        min(
            1.0,
            1.0 - (price / intent.max_price)
        )
    )


def calculate_brand_score(
    brand: str,
    intent: SearchIntent
) -> float:
    """
    Preferred brand = 1.0.
    Non-preferred brand = 0.3.
    No preference = neutral 0.5.
    """
    if not intent.preferred_brands:
        return 0.5

    preferred = {
        b.strip().lower()
        for b in intent.preferred_brands
    }

    return 1.0 if brand.strip().lower() in preferred else 0.3


def calculate_attribute_score(
    product: ProductResult
) -> float:
    """
    Attribute score is expected to be populated by retrieval
    or a future attribute-matching component.

    For now, ProductResult.attribute_score is already normalized.
    """
    return max(
        0.0,
        min(product.attribute_score, 1.0)
    )


def calculate_review_score(
    product: ProductResult
) -> float:
    """
    Combine review sentiment and confidence.

    Confidence prevents weak review evidence from dominating.
    """
    sentiment = max(
        0.0,
        min(product.review_sentiment_score, 1.0)
    )

    confidence = max(
        0.0,
        min(product.review_confidence, 1.0)
    )

    return sentiment * confidence


def calculate_deal_score(
    product: ProductResult
) -> float:
    """
    Placeholder until PriceComparisonAgent is integrated.

    price_score represents current price/deal quality.
    """
    return max(
        0.0,
        min(product.price_score, 1.0)
    )


def calculate_final_score(
    product: ProductResult
) -> float:

    semantic_score = max(
        0.0,
        min(product.semantic_score, 1.0)
    )

    rating_score = calculate_rating_score(
        product.rating
    )

    attribute_score = calculate_attribute_score(
        product
    )

    review_score = calculate_review_score(
        product
    )

    deal_score = calculate_deal_score(
        product
    )

    score = (
        0.40 * semantic_score
        + 0.15 * rating_score
        + 0.10 * product.price_score
        + 0.10 * product.brand_score
        + 0.10 * attribute_score
        + 0.10 * review_score
        + 0.05 * deal_score
    )

    return max(0.0, min(score, 1.0))


def rerank(
    products: list[ProductResult],
    intent: SearchIntent
) -> list[ProductResult]:

    for product in products:

        product.rating_score = calculate_rating_score(
            product.rating
        )

        product.price_score = calculate_price_score(
            product.price,
            intent
        )

        product.brand_score = calculate_brand_score(
            product.brand,
            intent
        )

        product.final_score = calculate_final_score(
            product
        )

    return sorted(
        products,
        key=lambda product: product.final_score,
        reverse=True
    )
