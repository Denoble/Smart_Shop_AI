

import json
import os
import sys
from pathlib import Path
from urllib import response

from httpx2 import query

from smartShopAi.models.pydantic_models import Product, Review, SearchIntent
from smartShopAi.database. embedding_model import *
from smartShopAi.database.embedding_query import *
from smartShopAi.read_env_variables.read_env_variable_file  import get_openai_api_key
from openai import OpenAI



class QueryUnderstandingAgent:

    def __init__(self):

        self.client = OpenAI(
            api_key=get_openai_api_key()
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-4.1-mini"
        )

    def understand(
        self,
        query: str
    ) -> SearchIntent:

        system_prompt = """
    You are the SmartShop Query Understanding Agent.

    IMPORTANT:
    Your response MUST be a valid JSON object.
    The output format is JSON.
    Return JSON only.
    Do not return Markdown.
    Do not return explanations.

    Convert the user's natural-language shopping request
    into a structured SearchIntent.

    You ONLY extract shopping intent.

    DO NOT:
    - search for products
    - recommend products
    - generate SQL
    - calculate prices
    - invent information
    - make purchasing decisions

    HARD CONSTRAINTS:
    Requirements that a product MUST satisfy.

    SOFT PREFERENCES:
    Things the user prefers but may compromise on.

    The JSON object MUST contain exactly these fields:

    {
        "semantic_query": "string",
        "brands": [],
        "category": null,
        "subcategory": null,
        "min_price": null,
        "max_price": null,
        "min_rating": null,
        "required_attributes": {},
        "preferred_attributes": {},
        "preferred_brands": []
    }

    Use:
    - [] for empty lists
    - {} for empty dictionaries
    - null for unspecified optional scalar values

    Return ONLY JSON.
    """
        response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                text={
                    "format": {
                        "type": "json_object"
                    }
                }
            )
        raw_json = response.output_text
        print("PRINTING RAW DATA")
        print(raw_json)
        data = json.loads(raw_json)
        return SearchIntent.model_validate_json(raw_json)
  
