from pydantic import BaseModel, Field


class StorePrice(BaseModel):
    store_id: str
    store_name: str
    price: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    shipping_cost: float = Field(default=0, ge=0)
    total_cost: float = Field(ge=0)
    savings: float = Field(default=0, ge=0)
    available: bool = True


class PriceComparison(BaseModel):
    product_id: str
    prices: list[StorePrice] = Field(default_factory=list)
    best_store_id: str | None = None
    best_store_name: str | None = None
    best_price: float | None = None
    savings_vs_highest: float = 0.0
