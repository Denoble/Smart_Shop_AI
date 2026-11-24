

import os
from pathlib import Path
from collections import defaultdict


from smartShopAi.database. embedding_query import get_db_connection
from smartShopAi.read_env_variables. read_env_variable_file import get_openai_api_key
from  smartShopAi.database. embedding_query import get_db_connection, get_product_reviews

class ReviewIntelligenceAgent:

    def __init__(self):
        self.client = OpenAI(
            api_key=get_openai_api_key()
            
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-4.1-mini"
        )

    def analyze(
        self,
        product_name: str,
        reviews: list[str]
    ) -> ReviewAnalysis:

        review_text = "\n\n".join(
            f"Review {i + 1}: {review}"
            for i, review in enumerate(reviews)
        )

        system_prompt = """
You are the SmartShop Review Intelligence Agent.

Analyze customer reviews for a product.

Extract:

1. Pros
2. Cons
3. Product aspects mentioned by customers
4. Sentiment for each aspect

Aspect sentiment must be between:

-1.0 = extremely negative
 0.0 = neutral
+1.0 = extremely positive

Do not invent information.

Only report information supported
by the provided reviews.

Return ONLY the structured response.
"""

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": (
                        f"Product: {product_name}\n\n"
                        f"{review_text}"
                    )
                }
            ],
            text_format=ReviewAnalysis
        )

        return response.output_parsed










class ReviewIntelligenceService:

    def __init__(self, connection):
        self.connection = get_db_connection()
        self.agent = ReviewIntelligenceAgent()

    def analyze_product(
        self,
        product_id: str,
        product_name: str
    ):

        reviews = get_product_reviews(
            self.connection,
            product_id
        )

        if not reviews:
            return None

        analysis = self.agent.analyze(
            product_name,
            reviews
        )

        aspects = defaultdict(list)

        for aspect in analysis.aspects:
            aspects[aspect.name.lower()].append(
                aspect.sentiment
            )

        aspect_summary = {
            name: {
                "sentiment": sum(scores) / len(scores),
                "mentions": len(scores)
            }
            for name, scores in aspects.items()
        }

        return {
            "pros": analysis.pros,
            "cons": analysis.cons,
            "aspects": aspect_summary
        }
