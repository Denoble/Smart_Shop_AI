import math
from multiprocessing import connection
import sys
import unittest
from pathlib import Path
import pytest




model_directory = Path("./models")
database_directory = Path("./database")
agents_directory = Path("./agents")
search_directory = Path("./search")
sys.path.append(str(database_directory))
sys.path.append(str(model_directory))
sys.path.append(str(agents_directory))
sys.path.append(str(search_directory))


from recommendation_agent import RecommendationAgent
from query_parser import parse_query
from pydantic_models import Product, Review
from embedding_model import *
from embedding_query import *
from understanding_agent import *
from semantic_search import *
from shopping_agent import ShoppingAgent


query_agent = (
        QueryUnderstandingAgent()
    )

embedding_model = (
        EmbeddingModel()
    )

def test_smartshop_retriever_pipeline():
    query = """
    I'm looking for a laptop for software development
    under $1,200. I prefer Lenovo or Dell,
    but I'm open to other brands. I need at least
    16GB RAM and excellent battery life.
    """

    with get_db_connection() as connection:

        retriever = SmartShopRetriever(
            connection,
            embedding_model,
            query_agent
        )

        intent, results = retriever.search(
            query,
            limit=10
        )

        print("\nSEARCH INTENT")
        print("=" * 60)

        print(
            intent.model_dump_json(
                indent=2
            )
        )

        print("\nRESULTS")
        print("=" * 60)

        for result in results:

            print(
                f"""
    {result.name}
    Brand: {result.brand}
    Price: ${result.price:.2f}
    Rating: {result.rating}
    Semantic: {result.semantic_score:.4f}
    Final: {result.final_score:.4f}
    """
            )

def test_query_parser():
    queries = [
        """
        Find me a Dell laptop under $1500
        with at least 16GB RAM
        """,

        """
        I need a Lenovo laptop below $1200
        with at least 4 stars
        """,

        """
        Find me an Apple laptop over $1000
        """,
    ]
    
    agent = QueryUnderstandingAgent()

    for query in queries:

        print("=" * 60)

        print("QUERY:")
        print(query.strip())

        result = agent.understand(query)

        print("\nPARSED:")
        print(result.model_dump())




def test_recommendation_agent(retriever: SmartShopRetriever,
                            db_connection:Connection, embedding_model: EmbeddingModel,
                        query_agent: QueryUnderstandingAgent):
            shopping_agent = ShoppingAgent(retriever, db_connection)
            result = shopping_agent.recommend(
            """
            Find me a laptop for software development
            under $1200 with at least 16GB RAM
            and excellent battery life.
            """,
            user_preferences={
                "preferred_brands": ["Lenovo", "Dell"]
            }
        )
            print(result)
            for recommendation in (
                result["recommendations"].recommendations
            ):
                print(
                    recommendation.product_id,
                    recommendation.score,
                    recommendation.reason
                )

                

def test_query_understandingAgent():
    
    agent = QueryUnderstandingAgent()

    query = """
    I'm looking for a laptop for software development
    under $1,200. I prefer Lenovo or Dell,
    but I'm open to other brands. I need at least
    16GB RAM and I'd really like excellent battery life.
    """

    intent = agent.understand(query)

    print("\nUSER QUERY")
    print("=" * 60)
    print(query.strip())

    print("\nSEARCH INTENT")
    print("=" * 60)

    print(
        intent.model_dump_json(
            indent=2
        )
    )


 


def test_recommendation_agent():
    agent = RecommendationAgent()
    products=[
                ProductResult(
                    product_id="LP0001",
                    name="Test Laptop 1",
                    brand="Dell",
                    category="Laptop",
                    price=1000,
                    rating=4.5, 
                    semantic_score=0.9,
                    review_sentiment_score=0.9,
                    review_confidence=0.8
                )
            ]
    user_preferences = {
        "preferred_brands": ["Dell"]
    }
    recommendations = agent.recommend(
        products,
        user_preferences=user_preferences,
        limit=5
    )
    print(f"Recommendations: {recommendations.recommendations}")
    

# tests/test_pricing.py

def test_total_cost():

    price = 1000
    discount = 100
    shipping = 25

    total = (
        price
        - discount
        + shipping
    )

    assert total == 925
def test_review_confidence():

    review_count = 25

    confidence = min(
        review_count / 100.0,
        1.0
    )

    assert confidence == 0.25

def test_sentiment_normalization():

    assert normalize_sentiment(-1.0) == 0.0
    assert normalize_sentiment(0.0) == 0.5
    assert normalize_sentiment(1.0) == 1.0 
    
def test_review_score():

    product = ProductResult(
        product_id="LP0003",
        name="Test Laptop",
        brand="Dell",
        category="Laptop",
        price=1000,
        rating=4.5,
        semantic_score=0.9,
        review_sentiment_score=0.9,
        review_confidence=0.8
    )

    score = calculate_review_score(product)
    print(f"Review score for {product.name}: {score:.2f}")
    expected_score = 0.72
    assert score == pytest.approx(expected_score, rel=1e-2), f"Expected score to be approximately {expected_score}, but got {score:.2f}"
   
def test_shopping_agent_recommendation():
    db_connection = get_db_connection()
    embedding_model = EmbeddingModel()
    query_agent = QueryUnderstandingAgent()
    retriever = SmartShopRetriever(
        db_connection,
        embedding_model=embedding_model,
        query_agent=query_agent
    )
    shopping_agent = ShoppingAgent(
        retriever,
        db_connection   
    )
    result = shopping_agent.recommend(
        """
        Find me a laptop for software development
        under $1200 with at least 16GB RAM
        and excellent battery life.
        """,
        user_preferences={
            "preferred_brands": ["Lenovo", "Dell"]
        }
    )

    print(f"Shopping Agent Recommendations: {result['recommendations'].recommendations}") 
def test_build_filters():
    intent = SearchIntent(
    semantic_query="laptop for software development",
    max_price=1200,
    min_rating=4.0,
    required_attributes={
        "RAM": "16GB",
        "Storage": "512GB"
    },
    preferred_brands=["Dell", "Lenovo"]
)

    conditions, params = build_filters(intent)

    print("CONDITIONS:")
    for condition in conditions:
        print(condition)

    print("\nPARAMETERS:")
    print(params)
    
    
def test_hybrid_search(connection, embedding_model):

    intent = SearchIntent(
        semantic_query="laptop for software development",
        max_price=1200,
        required_attributes={
            "RAM": "16GB",
            "Storage": "512GB"
        }
    )

    results = hybrid_search(
        connection=connection,
        model=embedding_model,
        intent=intent,
        candidate_limit=10
    )

    print("\nRESULTS")
    print("=" * 60)

    assert isinstance(results, list)

    for product in results:

        print(
            f"{product.product_id} | "
            f"{product.name} | "
            f"{product.brand} | "
            f"${product.price:.2f} | "
            f"rating={product.rating} | "
            f"semantic={product.semantic_score:.4f}"
        )

        assert isinstance(product.product_id, str)
        assert isinstance(product.name, str)
        assert isinstance(product.semantic_score, float)
        
def test_hybrid_search_hard_filters(connection, embedding_model):
    intent = SearchIntent(
    semantic_query="laptop for software development",
    max_price=1200,
    min_rating=4.0,
    required_attributes={
        "RAM": "16GB",
        "Storage": "512GB"
    }
)

    results = hybrid_search(
        connection,
        embedding_model,
        intent,
        candidate_limit=10
    )

    for product in results:
        print(
            product.product_id,
            product.name,
            product.brand,
            product.price,
            product.rating,
            product.semantic_score
        )

    assert all(product.price <= 1200 for product in results)
    assert all(product.rating >= 4.0 for product in results)
        
def test_hybrid_search_without_filters(connection, embedding_model):
    intent = SearchIntent(
        semantic_query="laptop for programming")

    results = hybrid_search(
                connection,
                embedding_model,
                intent,
                candidate_limit=5
            )

    for product in results:
        print(
            product.product_id,
            product.name,
            product.semantic_score
        )
    
def test_end_to_end(shopping_agent):
    query =  """
            Find me a laptop for software development
            under $1200 with at least 16GB RAM
            and excellent battery life.
            """,
    product = ProductResult(
                product_id="LP0003",
                name="Test Laptop",
                brand="Dell",
                category="Laptop",
                price=1000,
                rating=4.5,
                semantic_score=0.9,
                review_sentiment_score=0.9,
                review_confidence=0.8
            )
    user_preferences={
                "preferred_brands": [
                    "Lenovo",
                    "Dell"
                ]
            }
    result = shopping_agent.recommend( query, user_preferences=user_preferences)
    

    assert result["intent"] is not None
    print(f"Intent: {result['intent']}")
    recommendations = (
        result["recommendations"]
        .recommendations
    )
    print(f"Recommendations length: {len(recommendations)}")
    assert len(recommendations) > 0

    for recommendation in recommendations:

        assert recommendation.product_id > 0
        assert 0 <= recommendation.score <= 1
        assert recommendation.reason
    
if __name__ == "__main__":
    #main()
    #test_query_parser()
    #test_smartshop_pipeline()
    db_connection = get_db_connection()
    embedding_model = EmbeddingModel()
    query_agent = QueryUnderstandingAgent()
    retriever = SmartShopRetriever(
        db_connection,
        embedding_model=embedding_model,
        query_agent=query_agent
    )
    #test_build_filters()
    #test_hybrid_search(db_connection, embedding_model)
    test_hybrid_search_hard_filters(db_connection, embedding_model)
    #test_hybrid_search_without_filters(db_connection, embedding_model)
    
    #test_smartshop_retriever_pipeline()
    #test_recommendation_agent()
    """shopping_agent = ShoppingAgent(
        retriever,
        db_connection   
    )
    #test_recommendation_agent()
    #test_query_understandingAgent()
    test_shopping_agent_recommendation()
    test_end_to_end(ShoppingAgent(
       retriever,
        db_connection
    ))"""
