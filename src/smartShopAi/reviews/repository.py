# ai/reviews/repository.py

from smartShopAi.reviews.aggregation import calculate_review_statistics


class ReviewRepository:

    def get_review_insight(
        self,
        connection,
        product_id: str
    ):

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    sentiment,
                    sentiment_score
                FROM reviews
                WHERE product_id = %s
                """,
                (product_id,)
            )

            rows = cursor.fetchall()

        return calculate_review_statistics(rows)
