import pytest

from pathlib import Path
import sys


from smartShopAi.database.embedding_model import EmbeddingModel
from smartShopAi.database.embedding_query import *
from smartShopAi.database.query_parser import *

from smartShopAi.models.pydantic_models  import ProductResult, SearchIntent

from smartShopAi.search.rerank import (
    calculate_rating_score,
    calculate_price_score,
    calculate_brand_score,
    calculate_attribute_score,
    calculate_review_score,
    calculate_deal_score,
    calculate_final_score,
    rerank,
)


def product(**overrides) -> ProductResult:
    defaults = {
        "product_id": "P001",
        "name": "Test Laptop",
        "brand": "Dell",
        "category": "Laptop",
        "price": 1000.0,
        "rating": 4.0,
        "semantic_score": 0.8,
        "attribute_score": 0.8,
        "rating_score": 0.0,
        "price_score": 0.0,
        "brand_score": 0.0,
        "review_sentiment_score": 0.8,
        "review_confidence": 1.0,
        "pros": [],
        "cons": [],
        "best_store": None,
        "best_total_price": None,
        "final_score": 0.0,
    }

    defaults.update(overrides)

    return ProductResult(**defaults)


# ---------------------------------------------------------
# Rating score
# ---------------------------------------------------------

def test_rating_score_minimum():
    assert calculate_rating_score(1) == pytest.approx(0.2)


def test_rating_score_middle():
    assert calculate_rating_score(3) == pytest.approx(0.6)


def test_rating_score_maximum():
    assert calculate_rating_score(5) == pytest.approx(1.0)


def test_rating_score_above_max_is_clamped():
    assert calculate_rating_score(6) == 1.0


def test_rating_score_below_min_is_clamped():
    assert calculate_rating_score(-1) == 0.0


# ---------------------------------------------------------
# Price score
# ---------------------------------------------------------

def test_price_score_without_budget():
    intent = SearchIntent(
        semantic_query="laptop"
    )

    assert calculate_price_score(1000, intent) == 0.5


def test_price_score_at_budget():
    intent = SearchIntent(
        semantic_query="laptop",
        max_price=1000
    )

    assert calculate_price_score(1000, intent) == 0.0


def test_price_score_below_budget():
    intent = SearchIntent(
        semantic_query="laptop",
        max_price=1000
    )

    assert calculate_price_score(500, intent) == 0.5


def test_price_score_zero_price():
    intent = SearchIntent(
        semantic_query="laptop",
        max_price=1000
    )

    assert calculate_price_score(0, intent) == 1.0


def test_price_score_above_budget():
    intent = SearchIntent(
        semantic_query="laptop",
        max_price=1000
    )

    assert calculate_price_score(1200, intent) == 0.0


def test_price_score_zero_budget_zero_price():
    intent = SearchIntent(
        semantic_query="laptop",
        max_price=0
    )

    assert calculate_price_score(0, intent) == 1.0


def test_price_score_zero_budget_positive_price():
    intent = SearchIntent(
        semantic_query="laptop",
        max_price=0
    )

    assert calculate_price_score(1, intent) == 0.0


# ---------------------------------------------------------
# Brand score
# ---------------------------------------------------------

def test_brand_score_without_preference():
    intent = SearchIntent(
        semantic_query="laptop"
    )

    assert calculate_brand_score(
        "Dell",
        intent
    ) == 0.5


def test_brand_score_preferred_brand():
    intent = SearchIntent(
        semantic_query="laptop",
        preferred_brands=["Dell"]
    )

    assert calculate_brand_score(
        "Dell",
        intent
    ) == 1.0


def test_brand_score_case_insensitive():
    intent = SearchIntent(
        semantic_query="laptop",
        preferred_brands=["dElL"]
    )

    assert calculate_brand_score(
        "DELL",
        intent
    ) == 1.0


def test_brand_score_non_preferred_brand():
    intent = SearchIntent(
        semantic_query="laptop",
        preferred_brands=["Lenovo"]
    )

    assert calculate_brand_score(
        "Dell",
        intent
    ) == 0.3


def test_brand_score_multiple_preferences():
    intent = SearchIntent(
        semantic_query="laptop",
        preferred_brands=["Lenovo", "Dell"]
    )

    assert calculate_brand_score(
        "Dell",
        intent
    ) == 1.0


# ---------------------------------------------------------
# Attribute score
# ---------------------------------------------------------

def test_attribute_score_is_preserved():
    p = product(attribute_score=0.75)

    assert calculate_attribute_score(p) == 0.75


def test_attribute_score_clamped_above_one():
    p = product(attribute_score=2.0)

    assert calculate_attribute_score(p) == 1.0


def test_attribute_score_clamped_below_zero():
    p = product(attribute_score=-1.0)

    assert calculate_attribute_score(p) == 0.0


# ---------------------------------------------------------
# Review score
# ---------------------------------------------------------

def test_review_score_full_confidence():
    p = product(
        review_sentiment_score=0.8,
        review_confidence=1.0
    )

    assert calculate_review_score(p) == pytest.approx(0.8)


def test_review_score_partial_confidence():
    p = product(
        review_sentiment_score=0.8,
        review_confidence=0.5
    )

    assert calculate_review_score(p) == pytest.approx(0.4)


def test_review_score_zero_confidence():
    p = product(
        review_sentiment_score=1.0,
        review_confidence=0.0
    )

    assert calculate_review_score(p) == 0.0


def test_review_score_negative_sentiment_is_clamped():
    p = product(
        review_sentiment_score=-1.0,
        review_confidence=1.0
    )

    assert calculate_review_score(p) == 0.0


def test_review_score_above_one_is_clamped():
    p = product(
        review_sentiment_score=2.0,
        review_confidence=2.0
    )

    assert calculate_review_score(p) == 1.0


# ---------------------------------------------------------
# Deal score
# ---------------------------------------------------------

def test_deal_score():
    p = product(price_score=0.7)

    assert calculate_deal_score(p) == 0.7


def test_deal_score_clamped():
    p = product(price_score=2.0)

    assert calculate_deal_score(p) == 1.0


# ---------------------------------------------------------
# Final score
# ---------------------------------------------------------

def test_final_score_is_between_zero_and_one():
    p = product(
        semantic_score=1.0,
        rating=5.0,
        price_score=1.0,
        brand_score=1.0,
        attribute_score=1.0,
        review_sentiment_score=1.0,
        review_confidence=1.0,
    )

    score = calculate_final_score(p)

    assert 0.0 <= score <= 1.0
    assert score == pytest.approx(1.0)


def test_final_score_zero_signals():
    p = product(
        semantic_score=0.0,
        rating=1.0,
        price_score=0.0,
        brand_score=0.0,
        attribute_score=0.0,
        review_sentiment_score=0.0,
        review_confidence=0.0,
    )

    score = calculate_final_score(p)

    assert score == pytest.approx(0.03)


def test_semantic_score_has_largest_weight():
    base = product(
        semantic_score=0.0,
        rating=5.0,
        price_score=1.0,
        brand_score=1.0,
        attribute_score=1.0,
        review_sentiment_score=1.0,
        review_confidence=1.0,
    )

    semantic = product(
        semantic_score=1.0,
        rating=5.0,
        price_score=1.0,
        brand_score=1.0,
        attribute_score=1.0,
        review_sentiment_score=1.0,
        review_confidence=1.0,
    )

    assert (
        calculate_final_score(semantic)
        >
        calculate_final_score(base)
    )


# ---------------------------------------------------------
# Re-ranking
# ---------------------------------------------------------

def test_rerank_returns_products_sorted_descending():
    intent = SearchIntent(
        semantic_query="laptop"
    )

    products = [
        product(
            product_id="P1",
            semantic_score=0.4,
        ),
        product(
            product_id="P2",
            semantic_score=0.9,
        ),
        product(
            product_id="P3",
            semantic_score=0.6,
        ),
    ]

    results = rerank(products, intent)

    assert [
        p.product_id for p in results
    ] == ["P2", "P3", "P1"]


def test_rerank_populates_scores():
    intent = SearchIntent(
        semantic_query="laptop",
        max_price=1200,
        preferred_brands=["Dell"]
    )

    p = product(
        brand="Dell",
        price=800,
        rating=4.5,
    )

    results = rerank([p], intent)

    result = results[0]

    assert result.rating_score == pytest.approx(0.9)
    assert result.price_score == pytest.approx(
        1 - (800 / 1200)
    )
    assert result.brand_score == 1.0
    assert 0.0 <= result.final_score <= 1.0


def test_rerank_empty_list():
    intent = SearchIntent(
        semantic_query="laptop"
    )

    assert rerank([], intent) == []


def test_rerank_preserves_product_id_as_string():
    intent = SearchIntent(
        semantic_query="laptop"
    )

    p = product(product_id="LP1980")

    result = rerank([p], intent)[0]

    assert isinstance(result.product_id, str)
    assert result.product_id == "LP1980"


def test_rerank_does_not_change_number_of_products():
    intent = SearchIntent(
        semantic_query="laptop"
    )

    products = [
        product(product_id="P1"),
        product(product_id="P2"),
        product(product_id="P3"),
    ]

    results = rerank(products, intent)

    assert len(results) == 3
