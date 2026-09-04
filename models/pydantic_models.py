from pydantic import BaseModel
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from openai import OpenAI
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



class Attribute(BaseModel):
    """
    A product attribute extracted from the user's request.
    """

    name: str = Field(
        description="The product attribute name, e.g. RAM, storage, weight."
    )

    value: str = Field(
        description="The attribute value, e.g. 16GB, 512GB, lightweight."
    )


class SearchIntent(BaseModel):
    """
    Structured representation of a user's shopping request.
    """

    model_config = ConfigDict(extra="forbid")

    semantic_query: str = Field(
        description=(
            "The semantic portion of the request used for "
            "vector search."
        )
    )

    brands: list[str] = Field(
        description="Brands explicitly required by the user."
    )

    category: Optional[str] = Field(
        description="Primary product category, or null."
    )

    subcategory: Optional[str] = Field(
        description="Product subcategory, or null."
    )

    min_price: Optional[float] = Field(
        description="Minimum acceptable price, or null."
    )

    max_price: Optional[float] = Field(
        description="Maximum acceptable price, or null."
    )

    min_rating: Optional[float] = Field(
        description="Minimum acceptable rating, or null."
    )

    required_attributes: list[Attribute] = Field(
        description=(
            "Hard product requirements. "
            "Return an empty list if there are none."
        )
    )

    preferred_attributes: list[Attribute] = Field(
        description=(
            "Soft product preferences. "
            "Return an empty list if there are none."
        )
    )

    preferred_brands: list[str] = Field(
        description=(
            "Brands the user prefers but does not require. "
            "Return an empty list if there are none."
        )
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
