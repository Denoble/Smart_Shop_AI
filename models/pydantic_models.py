from pydantic import BaseModel

class Product(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool
    brand: str
    category: str
    description: str
    stock: int
    rating: float
    
class Review(BaseModel):
    product_id: int
    rating: float
    text: str
    date: str
class StorePolicy(BaseModel):
    store_id: int
    policy_type: str
    description: str
    conditions: str
    timeframe: str
    
