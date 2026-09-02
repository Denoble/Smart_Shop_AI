from pydantic import BaseModel
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

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
    product_id: str
    rating: float
    text: str
    date: str
class Policy(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    policy_type: str
    description: str
    conditions: str
    timeframe: int
    
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

@dataclass
class ProductFilters:
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None

    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class SearchRequest:
    query: str
    filters: ProductFilters = field(
        default_factory=ProductFilters
    )

    limit: int = 10





class SearchIntent(BaseModel):
    """
    Structured representation of the user's shopping request.
    """

    semantic_query: str = Field(
        description=(
            "The semantic portion of the request that should "
            "be used for vector search."
        )
    )

    brands: list[str] = Field(
        default_factory=list
    )

    category: Optional[str] = None

    subcategory: Optional[str] = None

    min_price: Optional[float] = None

    max_price: Optional[float] = None

    min_rating: Optional[float] = None

    required_attributes: dict[str, str] = Field(
        default_factory=dict
    )

    preferred_attributes: dict[str, str] = Field(
        default_factory=dict
    )

    preferred_brands: list[str] = Field(
        default_factory=list
    )
class ProductResult(BaseModel):
    product_id: int

    name: str

    brand: str

    category: str

    price: float

    rating: float

    semantic_score: float

    attribute_score: float = 0.0

    rating_score: float = 0.0

    price_score: float = 0.0

    final_score: float = 0.0
