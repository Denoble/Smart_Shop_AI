import pytest
import sys
from pathlib import Path
sys.path.append(str(Path("./reviews")))

from smartShopAi.reviews. aggregation import (
    calculate_review_statistics,
)


def test_empty_reviews():
    result = calculate_review_statistics([])

    assert result["review_count"] == 0
    assert result["positive_ratio"] == 0.0
    assert result["negative_ratio"] == 0.0
    assert result["neutral_ratio"] == 0.0
    assert result["sentiment_score"] == 0.0
    assert result["confidence"] == 0.0


def test_single_positive_review():
    rows = [
        ("positive", 0.9)
    ]

    result = calculate_review_statistics(rows)

    assert result["review_count"] == 1
    assert result["positive_ratio"] == 1.0
    assert result["negative_ratio"] == 0.0
    assert result["neutral_ratio"] == 0.0
    assert result["sentiment_score"] == 0.9


def test_single_negative_review():
    rows = [
        ("negative", -0.8)
    ]

    result = calculate_review_statistics(rows)

    assert result["review_count"] == 1
    assert result["negative_ratio"] == 1.0
    assert result["sentiment_score"] == -0.8


def test_mixed_sentiments():
    rows = [
        ("positive", 0.8),
        ("positive", 0.6),
        ("negative", -0.8),
        ("neutral", 0.0),
    ]

    result = calculate_review_statistics(rows)

    assert result["review_count"] == 4

    assert result["positive_ratio"] == pytest.approx(0.5)
    assert result["negative_ratio"] == pytest.approx(0.25)
    assert result["neutral_ratio"] == pytest.approx(0.25)

    assert result["sentiment_score"] == pytest.approx(
        0.15
    )


def test_confidence_scales_with_review_count():
    rows = [
        ("positive", 0.8)
        for _ in range(10)
    ]

    result = calculate_review_statistics(rows)

    assert result["confidence"] == pytest.approx(0.5)


def test_confidence_reaches_one():
    rows = [
        ("positive", 0.8)
        for _ in range(20)
    ]

    result = calculate_review_statistics(rows)

    assert result["confidence"] == 1.0


def test_confidence_is_capped():
    rows = [
        ("positive", 0.8)
        for _ in range(100)
    ]

    result = calculate_review_statistics(rows)

    assert result["confidence"] == 1.0


def test_missing_sentiment_scores_are_ignored():
    rows = [
        ("positive", 0.8),
        ("negative", None),
        ("neutral", 0.0),
    ]

    result = calculate_review_statistics(rows)

    assert result["review_count"] == 3
    assert result["sentiment_score"] == pytest.approx(
        0.4
    )


def test_ratios_sum_to_one():
    rows = [
        ("positive", 0.8),
        ("positive", 0.7),
        ("negative", -0.8),
        ("neutral", 0.0),
    ]

    result = calculate_review_statistics(rows)

    total = (
        result["positive_ratio"]
        + result["negative_ratio"]
        + result["neutral_ratio"]
    )

    assert total == pytest.approx(1.0)
