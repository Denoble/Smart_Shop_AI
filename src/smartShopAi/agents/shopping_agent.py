

from smartShopAi.search. semantic_search import SmartShopRetriever
from smartShopAi.database.embedding_model import enrich_with_reviews,ReviewIntelligence
from smartShopAi.database.embedding_query import enrich_with_prices
from smartShopAi.search.rerank import rerank

class ShoppingAgent:

    def __init__(
        self,
        retriever,
        connection
    ):
        self.retriever = retriever
        self.connection = connection
        self.recommendation_agent = (
            RecommendationAgent()
        )

    def recommend(
        self,
        query: str,
        user_preferences: dict | None = None
    ) -> dict:

        intent, candidates = self.retriever.search(
            query,
            limit=20
        )

        candidates = enrich_with_reviews(
            self.connection,
            candidates
        )

        candidates = enrich_with_prices(
            self.connection,
            candidates
        )

        candidates = rerank(
            candidates,
            intent
        )

        recommendations = (
            self.recommendation_agent.recommend(
                candidates,
                user_preferences
            )
        )

        return {
            "intent": intent,
            "recommendations": recommendations
        }
