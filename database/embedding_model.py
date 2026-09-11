from sentence_transformers import SentenceTransformer



class EmbeddingModel:

    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return vector.tolist()
    

def product_to_text(product) -> str:
    return f"""
    Product: {product.name}
    Brand: {product.brand}
    Category: {product.category}
    Description:
    {product.description}
    Price:
    {product.price}

    """
    
def review_to_text(review) -> str:
    return f"""
    Product: {review.product_id}
    Rating:
    {review.rating}/5
     Sentiment:
        {review.text}
    Date:
    {review.date}
    """
def policy_to_text(policy) -> str:

    return f"""
     Policy_Type:
        {policy.policy_type}
        
    Description:
        {policy.description}
        
    Condition:
    {policy.conditions}
    
    Timeframe:
    {policy.timeframe}
    """


class ReviewIntelligence:

    def analyze_product(
        self,
        connection,
        product_id: int
    ) -> ReviewInsight:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS review_count,

                    COALESCE(
                        AVG(sentiment_score),
                        0
                    ) AS sentiment_score,

                    COALESCE(
                        AVG(
                            CASE
                                WHEN sentiment = 'positive'
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS positive_ratio,

                    COALESCE(
                        AVG(
                            CASE
                                WHEN sentiment = 'negative'
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS negative_ratio,

                    COALESCE(
                        AVG(
                            CASE
                                WHEN sentiment = 'neutral'
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS neutral_ratio

                FROM reviews
                WHERE product_id = %s
                """,
                (product_id,)
            )

            row = cursor.fetchone()

        review_count = row[0]
        sentiment_score = float(row[1])
        positive_ratio = float(row[2])
        negative_ratio = float(row[3])
        neutral_ratio = float(row[4])

        confidence = min(review_count / 100.0, 1.0)

        return ReviewInsight(
            product_id=product_id,
            review_count=review_count,
            positive_ratio=positive_ratio,
            negative_ratio=negative_ratio,
            neutral_ratio=neutral_ratio,
            sentiment_score=sentiment_score,
            confidence=confidence
        )


def enrich_with_reviews(
    connection,
    products: list[ProductResult]
):
    intelligence = ReviewIntelligence()

    for product in products:

        insight = intelligence.analyze_product(
            connection,
            product.product_id
        )

        product.review_sentiment_score = (
            insight.sentiment_score
        )

        product.review_confidence = (
            insight.confidence
        )

    return products
