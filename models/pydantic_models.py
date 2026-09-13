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
    product_id: str
    name: str
    brand: str
    category: str
    price: float
    rating: float

    semantic_score: float

    attribute_score: float = 0.0
    rating_score: float = 0.0
    price_score: float = 0.0
    brand_score: float = 0.0

    review_sentiment_score: float = 0.0
    review_confidence: float = 0.0

    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)

    best_store: str | None = None
    best_total_price: float | None = None

    final_score: float = 0.0



class AspectInsight(BaseModel):
    sentiment: float = 0.0
    mentions: int = 0


class ReviewInsight(BaseModel):
    product_id: int

    review_count: int = 0

    positive_ratio: float = 0.0
    negative_ratio: float = 0.0
    neutral_ratio: float = 0.0

    sentiment_score: float = 0.0
    confidence: float = 0.0

    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)

    aspects: dict[str, AspectInsight] = Field(
        default_factory=dict
    )


class Aspect(BaseModel):
    name: str
    sentiment: float = Field(
        ge=-1.0,
        le=1.0
    )


class ReviewAnalysis(BaseModel):
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    aspects: list[Aspect] = Field(default_factory=list)

class StorePrice(BaseModel):
    store_id: int
    store_name: str

    price: float
    discount: float = 0.0
    shipping_cost: float = 0.0

    total_cost: float
    savings: float = 0.0

    available: bool = True


class PriceComparison(BaseModel):
    product_id: int
    prices: list[StorePrice]

    best_store_id: int | None = None
    best_price: float | None = None
