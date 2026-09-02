import sys
from pathlib import Path

dir_path = Path("./models")
dir_path1 = Path("./database")
sys.path.append(str(dir_path1))
sys.path.append(str(dir_path))
from pydantic_models import *
from embedding_model import *
from embedding_query import *

products = read_product_file()


"""for product in products:
    input_text = product_to_text(product)
    embedding_model = EmbeddingModel()
    embedding_vector = embedding_model.embed(input_text)
    #insert_product_embedding(product.id, input_text, embedding_vector)
    insert_product(product)"""
    
policies = read_policy_file()
for policy in policies:
    input_text = policy_to_text(policy)
    embedding_model = EmbeddingModel()
    embedding_vector = embedding_model.embed(input_text)
    #insert_policy_embedding(policy.policy_type, input_text, embedding_vector)
    insert_policy(policy)
    
    
 
"""reviews = read_review_file()
for review in reviews:
    input_text = review_to_text(review)
    embedding_model = EmbeddingModel()
    embedding_vector = embedding_model.embed(input_text)
    #insert_review_embedding(review.product_id, input_text, embedding_vector)
    insert_review(review)"""
   
        

