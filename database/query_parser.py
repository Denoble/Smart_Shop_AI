import re
import os
import sys
from pathlib import Path


dir_path = Path("./models")
sys.path.append(str(dir_path))
from pydantic_models import SearchIntent


KNOWN_BRANDS = [
    "Apple",
    "Dell",
    "Lenovo",
    "HP",
    "Samsung",
    "Sony",
    "Bose",
    "Microsoft",
    "Asus",
    "Acer",
]

KNOWN_CATEGORIES = {
    "laptop": "Computers",
    "laptops": "Computers",
    "computer": "Computers",
    "computers": "Computers",
    "headphones": "Audio",
    "headphone": "Audio",
    "phone": "Mobile Phones",
    "phones": "Mobile Phones",
    "smartphone": "Mobile Phones",
    "smartphones": "Mobile Phones",
}


def extract_brands(query: str) -> list[str]:
    query_lower = query.lower()

    return [
        brand
        for brand in KNOWN_BRANDS
        if brand.lower() in query_lower
    ]


def extract_price_range(
    query: str
) -> tuple[float | None, float | None]:

    query_lower = query.lower()

    max_price = None
    min_price = None

    max_patterns = [
        r"under\s*\$?([\d,]+(?:\.\d+)?)",
        r"below\s*\$?([\d,]+(?:\.\d+)?)",
        r"less than\s*\$?([\d,]+(?:\.\d+)?)",
        r"up to\s*\$?([\d,]+(?:\.\d+)?)",
        r"maximum\s*\$?([\d,]+(?:\.\d+)?)",
    ]

    for pattern in max_patterns:

        match = re.search(
            pattern,
            query_lower
        )

        if match:
            max_price = float(
                match.group(1).replace(",", "")
            )
            break

    min_patterns = [
        r"over\s*\$?([\d,]+(?:\.\d+)?)",
        r"above\s*\$?([\d,]+(?:\.\d+)?)",
        r"more than\s*\$?([\d,]+(?:\.\d+)?)",
    ]

    for pattern in min_patterns:

        match = re.search(
            pattern,
            query_lower
        )

        if match:
            min_price = float(
                match.group(1).replace(",", "")
            )
            break

    return min_price, max_price


def extract_rating(
    query: str
) -> float | None:

    patterns = [
        r"at least\s+([\d.]+)\s*stars?",
        r"minimum\s+([\d.]+)\s*stars?",
        r"([\d.]+)\+\s*stars?",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            query.lower()
        )

        if match:
            return float(match.group(1))

    return None


def extract_category(
    query: str
) -> str | None:

    query_lower = query.lower()

    for keyword, category in KNOWN_CATEGORIES.items():

        if keyword in query_lower:
            return category

    return None


def extract_attributes(
    query: str
) -> dict[str, str]:

    query_lower = query.lower()

    attributes = {}

    ram_match = re.search(
        r"(\d+)\s*gb\s*(?:ram|memory)",
        query_lower
    )

    if ram_match:
        attributes["RAM"] = (
            f"{ram_match.group(1)}GB"
        )

    storage_match = re.search(
        r"(\d+)\s*(gb|tb)\s*(?:ssd|storage)",
        query_lower
    )

    if storage_match:

        attributes["Storage"] = (
            f"{storage_match.group(1)}"
            f"{storage_match.group(2)}"
        )

    return attributes


def parse_query(query: str) -> SearchIntent:

    brands = extract_brands(query)

    min_price, max_price = (
        extract_price_range(query)
    )

    min_rating = extract_rating(query)

    category = extract_category(query)

    attributes = extract_attributes(query)

    semantic_query = query

    return SearchIntent(
        semantic_query=semantic_query,
        brands=brands,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        attributes=attributes,
    )






