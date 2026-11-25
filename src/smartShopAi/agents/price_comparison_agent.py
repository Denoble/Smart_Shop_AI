import sys
import os
from pathlib import Path
from unittest import result
from collections import defaultdict



from smartShopAi.models. pydantic_models import PriceComparison, StorePrice

class PriceComparisonAgent:

    def compare(
        self,
        connection,
        product_id: int
    ) -> PriceComparison:
        try:

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
                    JOIN stores s
                        ON s.id = pp.store_id
                    WHERE pp.product_id = %s
                    AND pp.availability = TRUE
                    ORDER BY
                        (
                            pp.price
                            - pp.discount
                            + pp.shipping_cost
                        ) ASC
                    """,
                    (product_id,)
                )

                rows = cursor.fetchall()

            if not rows:
                return PriceComparison(
                    product_id=product_id,
                    prices=[]
                )

            raw_totals = [
                float(row[2])
                - float(row[3] or 0)
                + float(row[4] or 0)
                for row in rows
            ]

            lowest_price = min(raw_totals)

            prices = []

            for row, total in zip(rows, raw_totals):

                prices.append(
                    StorePrice(
                        store_id=row[0],
                        store_name=row[1],
                        price=float(row[2]),
                        discount=float(row[3] or 0),
                        shipping_cost=float(row[4] or 0),
                        total_cost=total,
                        savings=max(
                            0.0,
                            total - lowest_price
                        ),
                        available=row[5]
                    )
                )

            best = prices[0]

            return PriceComparison(
                product_id=product_id,
                prices=prices,
                best_store_id=best.store_id,
                best_price=best.total_cost
            )
        except Exception as e:
            print(f"Error comparing prices for product {product_id}: {e}", file=sys.stderr)
            raise ValueError(f"Error comparing prices for product {product_id}: {e}")
