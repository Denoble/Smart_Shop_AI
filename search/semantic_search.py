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
sys.path.append(str(dir_path))
sys.path.append(str(dir_path1))
from pydantic_models import *
from embedding_query import *
from embedding_model import *
from query_parser import *
from pydantic_models import ProductFilters

filters =  ProductFilters(max_price=1000.0)

def semantic_search(
    connection: Connection,
    model: EmbeddingModel,
    query: str,
    limit: int = 50
):
    connection = embedding_query.get_db_connection()
    query_embedding = model.embed(query)

    with connection.cursor() as cursor:
        try:
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
                
        except Exception as e:
            print(f" Query Error: {e.with_traceback}")
            conn.rollback()
        finally:
            # Close the cursor and connection
            cursor.close()
            conn.close()
            
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

def hybrid_search(
    connection: Connection,
    model: EmbeddingModel,
    request: SearchRequest,
) -> list[ProductResult]:

    query_embedding = model.embed(
        request.query
    )
    connection = embedding_query.get_db_connection()
    conditions, filter_params = (
        build_product_filters(
            request.filters
        )
    )

    where_clause = ""

    if conditions:
        where_clause = (
            "WHERE " +
            " AND ".join(conditions)
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
        request.limit
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
            semantic_score=float(row[6])
        )
        for row in rows
    ]
    
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
) -> tuple[list[str], list]:

    conditions = []
    params = []

    if intent.brands:
        conditions.append(
        "(" +
        " OR ".join(
            ["LOWER(p.brand) = LOWER(%s)"]
            * len(intent.brands)
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
        
    for attribute, value in intent.attributes.items():

        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM product_attributes pa
                WHERE pa.product_id = p.product_id
                AND LOWER(pa.attribute) = LOWER(%s)
                AND LOWER(pa.value) LIKE LOWER(%s)
            )
            """
        )

    params.extend([
        attribute,
        f"%{value}%"
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





def main():

    query = """
    I'm looking for a Lenovo or Dell laptop
    under $1200 with at least 16GB RAM
    and excellent battery life.
    """

    model = EmbeddingModel()

    with get_db_connection() as connection:

        intent, results = search(
            connection,
            model,
            query
        )

        print("\nQUERY")
        print("=" * 60)
        print(query.strip())

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
Rating Score: {result.rating_score:.4f}
Price Score: {result.price_score:.4f}
Final Score: {result.final_score:.4f}
"""
            )


if __name__ == "__main__":
    main()
