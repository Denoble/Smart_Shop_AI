import psycopg2 
import pandas as pd
import numpy as np
import math
import sys
from pathlib import Path
from pgvector.psycopg2 import register_vector


dir_path = Path("./models")
sys.path.append(str(dir_path))
from pydantic_models import *

def read_product_file(file_path = "csvs/products.csv") ->list[Product]:
    pd_products = pd.read_csv(file_path)
    products = []
    for _, row in pd_products.iterrows():
        product = Product(
            id=row['product_id'],
            name=row['name'],
            price=row['price'],
            brand=row['brand'],
            category=row['category'],
            description=row['description'].strip() if pd.notnull(row['description']) else "",
            stock=row['stock'],
            rating=row['rating']
        )
        products.append(product)
    return products

def read_review_file(file_path = "./../csvs/reviews.csv") ->list[dict]:
    pd_reviews = pd.read_csv(file_path)
    reviews = []
    for _, row in pd_reviews.iterrows():
        review = {
            "product_id": row['product_id'],
            "rating": row['rating'],
            "text": row['text'],
            "date": row['date']
        }
        reviews.append(review)
    return reviews

def read_policy_file(file_path = "./../csvs/policies.csv") ->list[dict]:
    pd_policies = pd.read_csv(file_path)
    policies = []
    for _, row in pd_policies.iterrows():
        policy = {
            "policy_type": row['policy_type'],
            "description": row['description'].strip() if pd.notnull(row['description']) else "",
            "conditions": row['conditions'],
            "timeframe": row['timeframe']
        }
        policies.append(policy)
    return policies
def insert_product_embedding(product_id, content, embedding):
    """
    Inserts a product embedding into the database.

    Args:
        product_id (int): The ID of the product.
        content (str): The textual content associated with the product.
        embedding (list[float]): The embedding vector for the product.
    """
    # Convert the embedding list to a string representation
    embedding_str = ','.join(map(str, embedding))

    # Establish a connection to the PostgreSQL database
    conn = psycopg2.connect(
        dbname="smartshop",
        user="smartshop",
        password="smartshop",
        host="localhost",
        port=5432
    )
    content = content.strip()
    register_vector(conn)
    cursor = conn.cursor()
    insert_query = """
                INSERT INTO product_embeddings (product_id, content, embedding)
                VALUES (%s, %s, %s)
                ON CONFLICT (product_id) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    created_at = CURRENT_TIMESTAMP;
            """
    try:
        # Execute the INSERT statement
        print(f"content is {content}")
        cursor.execute(insert_query, (product_id, content, embedding))
        
        # Commit the transaction
        conn.commit()
        print("Record inserted successfully!")
    except Exception as e:
        print(f"Error inserting product embedding: {e}")
        conn.rollback()
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()
