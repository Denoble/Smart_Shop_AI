from psycopg import Connection
import pandas as pd
import numpy as np
import math
import sys
from pathlib import Path
import psycopg
from pgvector.psycopg import register_vector

dir_path1 = Path("./database")
dir_path = Path("./models")
dir_path2 = Path("./agents")
sys.path.append(str(dir_path))
sys.path.append(str(dir_path1))
sys.path.append(str(dir_path2)) 
from pydantic_models import *
from embedding_query import *
from embedding_model import *
from query_parser import *
from pydantic_models import ProductFilters

filters =  ProductFilters(max_price=1000.0)


            
def build_product_filters(
    filters: ProductFilters = filters
):

    conditions = []
    params = []

    if filters.brand:
        conditions.append(
            "LOWER(p.brand) = LOWER(%s)"
        )
        params.append(filters.brand)

    if filters.category:
        conditions.append(
            "LOWER(p.category) = LOWER(%s)"
        )
        params.append(filters.category)

    if filters.subcategory:
        conditions.append(
            "LOWER(p.subcategory) = LOWER(%s)"
        )
        params.append(filters.subcategory)

    if filters.min_price is not None:
        conditions.append(
            "p.price >= %s"
        )
        params.append(filters.min_price)

    if filters.max_price is not None:
        conditions.append(
            "p.price <= %s"
        )
        params.append(filters.max_price)

    if filters.min_rating is not None:
        conditions.append(
            "p.rating >= %s"
        )
        params.append(filters.min_rating)

    return conditions, params


def search_products(
    connection: Connection =conn,
    model: EmbeddingModel = EmbeddingModel(),
    query: str= "",
    limit: int = 5
):

    query_embedding = model.embed(query)

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT
                product_id,
                name,
                brand,
                category,
                price,
                rating,

                1 - (
                    embedding
                    <=>
                    %s::vector
                ) AS similarity

            FROM product_embeddings 


            ORDER BY
                embedding <=> %s::vector

            LIMIT %s
        """, (
            query_embedding,
            query_embedding,
            limit
        ))

        return cursor.fetchall()

    
def semantic_search(
    connection: Connection,
    model: embedding_query.EmbeddingModel,
    query: str ,
    limit: int = 50
):
    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                p.product_id,
                p.name,
                p.brand,
                p.category,
                p.price,
                p.rating,

                1 - (
                    pe.embedding <=> %s::vector
                ) AS semantic_score

            FROM product_embeddings pe

            JOIN products p
                ON p.product_id = pe.product_id

            ORDER BY
                pe.embedding <=> %s::vector

            LIMIT %s
            """,
            (
                query_embedding,
                query_embedding,
                limit
            )
        )

        return cursor.fetchall()

def calculate_score(
    semantic_score: float,
    rating: float,
    price: float,
    max_price: float | None
) -> float:

    rating_score = rating / 5.0

    if max_price:
        price_score = max(
            0.0,
            1.0 - (price / max_price)
        )
    else:
        price_score = 0.5

    return (
        0.60 * semantic_score +
        0.15 * rating_score +
        0.15 * price_score
    )


def build_filters(
    intent: SearchIntent
):

    conditions = []
    params = []

    if intent.brands:

        conditions.append(
            "(" +
            " OR ".join(
                [
                    "LOWER(p.brand) = LOWER(%s)"
                    for _ in intent.brands
                ]
            ) +
            ")"
        )

        params.extend(intent.brands)

    if intent.category:

        conditions.append(
            "LOWER(p.category) = LOWER(%s)"
        )

        params.append(
            intent.category
        )

    if intent.subcategory:

        conditions.append(
            "LOWER(p.subcategory) = LOWER(%s)"
        )

        params.append(
            intent.subcategory
        )

    if intent.min_price is not None:

        conditions.append(
            "p.price >= %s"
        )

        params.append(
            intent.min_price
        )

    if intent.max_price is not None:

        conditions.append(
            "p.price <= %s"
        )

        params.append(
            intent.max_price
        )

    if intent.min_rating is not None:

        conditions.append(
            "p.rating >= %s"
        )

        params.append(
            intent.min_rating
        )

    # HARD attribute constraints
    for attribute in (
        intent.required_attributes
    ):

        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM product_attributes pa
                WHERE pa.product_id = p.product_id
                AND LOWER(pa.attribute)
                    = LOWER(%s)
                AND LOWER(pa.value)
                    LIKE LOWER(%s)
            )
            """
        )

        params.extend([
            attribute.name,
            f"%{attribute.value}%"
        ])

    return conditions, params

def hybrid_search(
    connection: Connection,
    model: EmbeddingModel,
    intent: SearchIntent,
    candidate_limit: int = 50,
) -> list[ProductResult]:

    query_embedding = model.embed(
        intent.semantic_query
    )

    conditions, filter_params = (
        build_filters(intent)
    )

    where_clause = ""

    if conditions:

        where_clause = (
            "WHERE\n" +
            "\nAND ".join(conditions)
        )

    sql = f"""
        SELECT
            p.product_id,
            p.name,
            p.brand,
            p.category,
            p.price,
            p.rating,

            1 - (
                pe.embedding <=> %s::vector
            ) AS semantic_score

        FROM product_embeddings pe

        JOIN products p
            ON p.product_id = pe.product_id

        {where_clause}

        ORDER BY
            pe.embedding <=> %s::vector

        LIMIT %s
    """

    params = [
        query_embedding,
        *filter_params,
        query_embedding,
        candidate_limit
    ]

    with connection.cursor() as cursor:

        cursor.execute(
            sql,
            params
        )

        rows = cursor.fetchall()

    return [
        ProductResult(
            product_id=row[0],
            name=row[1],
            brand=row[2],
            category=row[3],
            price=float(row[4]),
            rating=float(row[5]),
            semantic_score=float(row[6]),
        )
        for row in rows
    ]




def calculate_price_score(
    price: float,
    intent: SearchIntent
) -> float:

    if intent.max_price is None:
        return 0.5

    if price > intent.max_price:
        return 0.0

    return 1.0 - (
        price / intent.max_price
    )


def calculate_rating_score(
    rating: float
) -> float:

    return min(
        rating / 5.0,
        1.0
    )


def rerank(
    products: list[ProductResult],
    intent: SearchIntent
) -> list[ProductResult]:

    for product in products:

        product.rating_score = (
            calculate_rating_score(
                product.rating
            )
        )

        product.price_score = (
            calculate_price_score(
                product.price,
                intent
            )
        )

        product.attribute_score = (
            1.0
            if intent.attributes
            else 0.5
        )

        product.final_score = (
            0.60 * product.semantic_score
            +
            0.20 * product.rating_score
            +
            0.15 * product.price_score
            +
            0.05 * product.attribute_score
        )

    return sorted(
        products,
        key=lambda x: x.final_score,
        reverse=True
    )



def search(
    connection: Connection,
    model: EmbeddingModel,
    query: str,
    limit: int = 10
):

    # 1. Understand the user's query
    intent = parse_query(query)

    # 2. Retrieve candidates
    candidates = hybrid_search(
        connection,
        model,
        intent,
        candidate_limit=50
    )

    # 3. Re-rank candidates
    ranked = rerank(
        candidates,
        intent
    )

    # 4. Return top K
    return intent, ranked[:limit]


def validate_search_intent(
    intent: SearchIntent
) -> SearchIntent:

    if intent.min_price is not None:
        if intent.min_price < 0:
            raise ValueError(
                "Minimum price cannot be negative"
            )

    if intent.max_price is not None:
        if intent.max_price < 0:
            raise ValueError(
                "Maximum price cannot be negative"
            )

    if (
        intent.min_price is not None
        and intent.max_price is not None
        and intent.min_price > intent.max_price
    ):
        raise ValueError(
            "Minimum price cannot exceed maximum price"
        )

    if intent.min_rating is not None:

        if not 1 <= intent.min_rating <= 5:
            raise ValueError(
                "Rating must be between 1 and 5"
            )

    return intent



class SmartShopRetriever:

    def __init__(
        self,
        connection: Connection,
        embedding_model: EmbeddingModel,
        query_agent: QueryUnderstandingAgent
    ):

        self.connection = connection
        self.embedding_model = embedding_model
        self.query_agent = query_agent

    def search(
        self,
        query: str,
        limit: int = 10
    ):

        # 1. Natural language → structured intent
        intent = self.query_agent.understand(
            query
        )

        # 2. Validate LLM output
        intent = validate_search_intent(
            intent
        )

        # 3. Hybrid retrieval
        candidates = hybrid_search(
            self.connection,
            self.embedding_model,
            intent,
            candidate_limit=50
        )

        # 4. Re-rank
        ranked = rerank(
            candidates,
            intent
        )

        # 5. Return Top-K
        return intent, ranked[:limit]

