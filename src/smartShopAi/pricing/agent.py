from smartShopAi.pricing.models import StorePrice, PriceComparison


def calculate_total(
    price: float,
    discount: float = 0.0,
    shipping_cost: float = 0.0,
) -> float:
    if price < 0 or discount < 0 or shipping_cost < 0:
        raise ValueError("Price, discount and shipping must be non-negative")

    if discount > price:
        raise ValueError("Discount cannot exceed price")

    return round(price - discount + shipping_cost, 2)


def compare_prices(
    product_id: str,
    offers: list[dict],
) -> PriceComparison:
    prices = []

    for offer in offers:
        total = calculate_total(
            float(offer["price"]),
            float(offer.get("discount") or 0),
            float(offer.get("shipping_cost") or 0),
        )

        prices.append(
            StorePrice(
                store_id=str(offer["store_id"]),
                store_name=offer["store_name"],
                price=float(offer["price"]),
                discount=float(offer.get("discount") or 0),
                shipping_cost=float(offer.get("shipping_cost") or 0),
                total_cost=total,
                available=offer.get("available", True),
            )
        )

    available = [p for p in prices if p.available]
    available.sort(key=lambda p: (p.total_cost, p.store_name.lower()))

    if not available:
        return PriceComparison(product_id=product_id, prices=prices)

    best = available[0]
    highest = max(p.total_cost for p in available)

    for price in prices:
        price.savings = round(
            max(0.0, price.total_cost - best.total_cost), 2
        )

    return PriceComparison(
        product_id=product_id,
        prices=prices,
        best_store_id=best.store_id,
        best_store_name=best.store_name,
        best_price=best.total_cost,
        savings_vs_highest=round(highest - best.total_cost, 2),
    )


class PriceComparisonAgent:
    def compare(self, connection, product_id: str) -> PriceComparison:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pp.store_id,
                    s.name,
                    pp.price,
                    pp.discount,
                    pp.shipping_cost,
                    pp.availability
                FROM product_prices pp
                JOIN stores s ON s.id = pp.store_id
                WHERE pp.product_id = %s
                ORDER BY pp.captured_at DESC
                """,
                (product_id,),
            )
            rows = cursor.fetchall()

        # Keep the most recent offer per store.
        latest_by_store = {}
        for store_id, name, price, discount, shipping, available in rows:
            latest_by_store.setdefault(
                str(store_id),
                {
                    "store_id": str(store_id),
                    "store_name": name,
                    "price": price,
                    "discount": discount,
                    "shipping_cost": shipping,
                    "available": available,
                },
            )

        return compare_prices(product_id, list(latest_by_store.values()))
