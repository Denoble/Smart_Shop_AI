from pydantic import BaseModel
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class Currency(str, Enum):
    USD = "USD"
    CAD = "CAD"
    EUR = "EUR"

class Product(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    price: float
    brand: str
    category: str
    description: str
    stock: int
    rating: float
    
class Review(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    rating: float
    text: str
    date: str
class Policy(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    store_id: int
    policy_type: str
    description: str
    conditions: str
    timeframe: str
    
class Pricing(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    price: float = Field(gt=0)
    currency: Currency = Currency.USD
    discount_percentage: float = Field(
        default=0,
        ge=0,
        le=100
    )

    @property
    def final_price(self) -> float:
        """
        Calculate price after discount.
        """
        return round(
            self.price * (1 - self.discount_percentage / 100),
            2
        )

    
