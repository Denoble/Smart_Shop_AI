import sys
from pathlib import Path
dir_path = Path("./models")
dir_path1 = Path("./database")
sys.path.append(str(dir_path1))
sys.path.append(str(dir_path))
from pydantic_models import Product, Review
from embedding_model import *
from embedding_query import *

product = Product(
    id=1,
    name="Smartphone X",
    price=999.00,
    in_stock=True,
    brand="TechBrand",
    category="Electronics",
    description="A high-end smartphone with a sleek design and powerful features.",
    stock=50,
    rating=4.5
)
input_text = product_to_text(product)
embedding_model = EmbeddingModel()
embedding_vector = embedding_model.embed(input_text)
insert_product_embedding(product.id, input_text, embedding_vector)
