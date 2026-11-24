
def calculate_review_statistics(rows) -> dict:
    """
    rows:
        [(sentiment, sentiment_score), ...]
    """

    total = len(rows)

    if total == 0:
        return {
            "review_count": 0,
            "positive_ratio": 0.0,
            "negative_ratio": 0.0,
            "neutral_ratio": 0.0,
            "sentiment_score": 0.0,
            "confidence": 0.0,
        }

    positive = sum(
        1 for sentiment, _ in rows
        if sentiment == "positive"
    )

    negative = sum(
        1 for sentiment, _ in rows
        if sentiment == "negative"
    )

    neutral = sum(
        1 for sentiment, _ in rows
        if sentiment == "neutral"
    )

    scores = [
        float(score)
        for _, score in rows
        if score is not None
    ]

    sentiment_score = (
        sum(scores) / len(scores)
        if scores else 0.0
    )

    confidence = min(
        1.0,
        total / 20.0
    )

    return {
        "review_count": total,
        "positive_ratio": positive / total,
        "negative_ratio": negative / total,
        "neutral_ratio": neutral / total,
        "sentiment_score": sentiment_score,
        "confidence": confidence,
    }
