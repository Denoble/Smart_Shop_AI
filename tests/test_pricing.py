from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from smartShopAi.pricing.agent import (
    PriceComparisonAgent,
    calculate_total,
)


# ---------- Total-cost calculations ----------

@pytest.mark.parametrize(
    "price,discount,shipping,expected",
    [
        ("100", "0", "0", "100"),
        ("100", "10", "0", "90"),
        ("100", "10", "5", "95"),
        ("0", "0", "0", "0"),
        ("19.99", "2.50", "3.99", "21.48"),
    ],
)
def test_calculate_total(price, discount, shipping, expected):
    assert calculate_total(
        Decimal(price),
        Decimal(discount),
        Decimal(shipping),
    ) == Decimal(expected)


@pytest.mark.parametrize(
    "price,discount,shipping",
    [
        ("-1", "0", "0"),
        ("10", "-1", "0"),
        ("10", "0", "-1"),
        ("10", "11", "0"),
    ],
)
def test_invalid_costs_raise(price, discount, shipping):
    with pytest.raises(ValueError):
        calculate_total(
            Decimal(price),
            Decimal(discount),
            Decimal(shipping),
        )


# ---------- Database test helpers ----------

def make_connection(rows):
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchall.return_value = rows

    return connection, cursor


def offer(
    store_id,
    name,
    price,
    discount=0,
    shipping=0,
    available=True,
    captured_at="2026-10-24",
):
    return (
        store_id,
        name,
        Decimal(str(price)),
        Decimal(str(discount)),
        Decimal(str(shipping)),
        available,
        captured_at,
    )


# The agent query selects six columns in its current implementation.
def db_offer(
    store_id,
    name,
    price,
    discount=0,
    shipping=0,
    available=True,
):
    return (
        store_id,
        name,
        Decimal(str(price)),
        Decimal(str(discount)),
        Decimal(str(shipping)),
        available,
    )


# ---------- Comparison behaviour ----------

def test_cheapest_total_cost_wins():
    connection, _ = make_connection([
        db_offer("1", "Store A", 100, 0, 10),
        db_offer("2", "Store B", 105, 0, 0),
    ])

    result = PriceComparisonAgent().compare(connection, "LP1980")

    assert result.product_id == "LP1980"
    assert result.best_store_name == "Store B"
    assert result.best_price == 105.0


def test_discount_and_shipping_are_both_applied():
    connection, _ = make_connection([
        db_offer("1", "Store A", 120, 20, 5),
        db_offer("2", "Store B", 110, 0, 20),
    ])

    result = PriceComparisonAgent().compare(connection, "LP1980")

    assert result.best_store == "Store A"
    assert result.best_price == 105.0


def test_unavailable_offer_cannot_win():
    connection, _ = make_connection([
        db_offer("1", "Unavailable Store", 1, available=False),
        db_offer("2", "Available Store", 50),
    ])

    result = PriceComparisonAgent().compare(connection, "LP1980")

    assert result.best_store_name == "Available Store"
    assert result.best_price == 50.0


def test_all_offers_unavailable():
    connection, _ = make_connection([
        db_offer("1", "Store A", 50, available=False),
    ])

    result = PriceComparisonAgent().compare(connection, "LP1980")

    assert result.best_store_name is None
    assert result.best_price is None
    assert len(result.prices) == 1


def test_no_offers():
    connection, _ = make_connection([])

    result = PriceComparisonAgent().compare(connection, "LP1980")

    assert result.product_id == "LP1980"
    assert result.prices == []
    assert result.best_store is None
    assert result.best_price is None


def test_savings_are_relative_to_cheapest_offer():
    connection, _ = make_connection([
        db_offer("1", "Store A", 100),
        db_offer("2", "Store B", 130),
        db_offer("3", "Store C", 115),
    ])

    result = PriceComparisonAgent().compare(connection, "LP1980")

    savings = {
        item.store_name: item.savings
        for item in result.prices
    }

    assert savings["Store A"] == 0
    assert savings["Store B"] == 30
    assert savings["Store C"] == 15
    assert result.savings == 30


def test_tied_prices_have_deterministic_winner():
    connection, _ = make_connection([
        db_offer("1", "Store Z", 100),
        db_offer("2", "Store A", 100),
    ])

    result = PriceComparisonAgent().compare(connection, "LP1980")

    assert result.best_store == "Store A"


def test_product_id_remains_string():
    connection, _ = make_connection([
        db_offer("1", "Store A", 100),
    ])

    result = PriceComparisonAgent().compare(connection, "LP1980")

    assert isinstance(result.product_id, str)


@pytest.mark.parametrize("product_id", ["", "   ", None, 123])
def test_invalid_product_id_raises(product_id):
    connection, _ = make_connection([])

    with pytest.raises(ValueError):
        PriceComparisonAgent().compare(connection, product_id)


def test_query_uses_parameterized_product_id():
    connection, cursor = make_connection([])

    PriceComparisonAgent().compare(connection, "LP1980")

    args = cursor.execute.call_args.args
    assert args[1] == ("LP1980",)
    assert "%s" in args[0]


def test_price_results_expose_total_cost():
    connection, _ = make_connection([
        db_offer("1", "Store A", 100, 10, 5),
    ])

    result = PriceComparisonAgent().compare(connection, "LP1980")

    assert result.prices[0].total_cost == 95
    assert result.prices[0].available is True
