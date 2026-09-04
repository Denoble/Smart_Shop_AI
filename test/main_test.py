import sys
from pathlib import Path
dir_path = Path("./models")
dir_path1 = Path("./database")
dir_path2 = Path("./agents")
dir_path3 = Path("./search")
sys.path.append(str(dir_path1))
sys.path.append(str(dir_path))
sys.path.append(str(dir_path2))
sys.path.append(str(dir_path3))

from query_parser import parse_query
from pydantic_models import Product, Review
from embedding_model import *
from embedding_query import *
from understanding_agent import *
from semantic_search import *


query_agent = (
        QueryUnderstandingAgent()
    )

embedding_model = (
        EmbeddingModel()
    )

def test_smartshop_pipeline():
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






def main():

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


if __name__ == "__main__":
    #main()
    #test_query_parser()
    test_smartshop_pipeline()
