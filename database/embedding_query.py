
import pandas as pd
import numpy as np
import math
import sys
from pathlib import Path
import psycopg
from pgvector.psycopg import register_vector


dir_path = Path("./models")
sys.path.append(str(dir_path))
from pydantic_models import *

# Establish a connection to the PostgreSQL database
conn = psycopg.connect(
            dbname="smartshop",
            user="smartshop",
            password="smartshop",
            host="localhost",
            port=5432
        )

register_vector(conn)
cursor = conn.cursor()

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

def read_review_file(file_path = "csvs/reviews.csv") ->list[dict]:
    pd_reviews = pd.read_csv(file_path)
    reviews = []
    for _, row in pd_reviews.iterrows():
        review = Review (
                product_id = row['product_id'],
                rating = row['rating'],
                text = row['text'],
                date = row['date']
        )
        reviews.append(review)
    return reviews

def read_policy_file(file_path = "csvs/policies.csv") ->list[dict]:
    pd_policies = pd.read_csv(file_path)
    policies = []
    for _, row in pd_policies.iterrows():
        policy = Policy(
            policy_type =  row['policy_type'],
            description = row['description'].strip() if pd.notnull(row['description']) else "",
            conditions = row['conditions'],
            timeframe =row['timeframe']
        )
        policies.append(policy)
    return policies

def insert_product(product: Product):
    
    conn = get_db_connection()

    register_vector(conn)
    cursor = conn.cursor()
    query = """
    INSERT INTO products
(product_id, name, description, brand, category, subcategory,
 price, currency, rating, stock)
VALUES
(
    %s,
    %s,
    %s,
   %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s
)
 ON CONFLICT (product_id) 
                DO UPDATE SET 

name = EXCLUDED.name,
description = EXCLUDED.description,
brand = EXCLUDED.brand,
category = EXCLUDED.category,
subcategory = EXCLUDED.subcategory,
image_url = EXCLUDED.image_url,
price = EXCLUDED.price,
currency =EXCLUDED.currency,
rating = EXCLUDED.rating,
stock = EXCLUDED.stock,
created_at =EXCLUDED.created_at,
updated_at = CURRENT_TIMESTAMP
    """
    try:
        # Execute the INSERT statement
        cursor.execute(query, (product.id,
                            product.name, product.description,
                            product.brand,"","",product.price,
                            Currency.USD,product.rating,
                            product.stock))
        
        conn.commit()
        print("Record inserted successfully!")
    except Exception as e:
        print(f"Error inserting product: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_db_connection():
    conn = psycopg.connect(
            dbname="smartshop",
            user="smartshop",
            password="smartshop",
            host="localhost",
            port=5432
        )
    return conn
    
def insert_product_embedding(product_id, content, embedding):
    conn = get_db_connection()
    register_vector(conn)
    cursor = conn.cursor()
    """
    Inserts a product embedding into the database.

    Args:
        product_id (int): The ID of the product.
        content (str): The textual content associated with the product.
        embedding (list[float]): The embedding vector for the product.
    """
    # Convert the embedding list to a string representation
    embedding_str = ','.join(map(str, embedding))

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
        
def insert_policy_embedding(policy_type, content, embedding):
    
    conn = get_db_connection()
    content = content.strip()
    register_vector(conn)
    cursor = conn.cursor()
    insert_query = """
                INSERT INTO policy_embeddings (policy_type, content, embedding)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    created_at = CURRENT_TIMESTAMP;
            """
    try:
        # Execute the INSERT statement
        cursor.execute(insert_query, (policy_type, content, embedding))
        
        # Commit the transaction
        conn.commit()
        print(f"Record policy of  product {policy_type} inserted successfully!")
    except Exception as e:
        print(f"Error inserting policy embedding: {e}")
        conn.rollback()
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        
        
def insert_policy(policy: Policy):
    conn = get_db_connection()
    register_vector(conn)
    cursor = conn.cursor()
    
    insert_query = """
                INSERT INTO policies (type,
                description,conditions,timeframe)
                VALUES (%s, %s, %s,%s)
                ON CONFLICT (id) 
                DO UPDATE SET 
                    type = EXCLUDED.type,
                    description = EXCLUDED.description,
                    conditions = EXCLUDED.conditions,
                    timeframe = EXCLUDED.timeframe,
                    updated_at = CURRENT_TIMESTAMP;
            """
    try:
        # Execute the INSERT statement
        cursor.execute(insert_query, (policy.policy_type, policy.description, policy.conditions,
                                    policy.timeframe))
        
        # Commit the transaction
        conn.commit()
        print(f"Record product of product policy of type {policy.policy_type} inserted successfully!")
    except Exception as e:
        print(f"Error inserting policy: {e}")
        conn.rollback()
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()
    

def  insert_review_embedding(product_id, input_text, embedding):
     # Establish a connection to the PostgreSQL database
    
        conn = get_db_connection()
        content = input_text.strip()
        register_vector(conn)
        cursor = conn.cursor()
        insert_query = """
                        INSERT INTO review_embeddings (product_id, content, embedding)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (product_id) 
                        DO UPDATE SET 
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            created_at = CURRENT_TIMESTAMP;
                    """
        try:
            # Execute the INSERT statement
            cursor.execute(insert_query, (product_id, content, embedding))
    
            # Commit the transaction
            conn.commit()
            print("Record inserted successfully!")
        except Exception as e:
            print(f"Error inserting review embedding: {e}")
            conn.rollback()
        finally:
            # Close the cursor and connection
            cursor.close()
            conn.close()
        
    
    
def  insert_review(review:Review):

    conn = get_db_connection()
    register_vector(conn)
    cursor = conn.cursor()

    # Establish a connection to the PostgreSQL database
    insert_query = """
                    INSERT INTO reviews (product_id, rating, text,date,verified_purchase,
                    sentiment,sentiment_score)
                    VALUES (%s, %s, %s,%s,%s,%s,%s)
                    ON CONFLICT (product_id) 
                    DO UPDATE SET 
                        rating = EXCLUDED.rating,
                        text = EXCLUDED.text,
                        date = EXCLUDED.date,
                        verified_purchase = EXCLUDED.verified_purchase,
                        sentiment =EXCLUDED.sentiment,
                        sentiment_score =EXCLUDED.sentiment_score
                """
    try:
        # Execute the INSERT statement
        cursor.execute(insert_query, (review.product_id, review.rating,
                                    review.text,review.date,True,"",0))

        # Commit the transaction
        conn.commit()
        print("Record inserted successfully!")
    except Exception as e:
        print(f"Error inserting review : {e}")
        conn.rollback()
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()
    