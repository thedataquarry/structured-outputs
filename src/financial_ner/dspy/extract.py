"""
Run a DSPy pipeline to extract financial entities from unstructured text
and output the results to newline-delimited JSON files.
"""

import argparse
import asyncio
import json
import os
from typing import Any

import dspy
import polars as pl
from dspy.adapters.baml_adapter import BAMLAdapter
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# Using OpenRouter. Switch to another LLM provider as needed
lm = dspy.LM(
    model="openrouter/mistralai/ministral-14b-2512",
    api_base="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    cache=False,
)
dspy.configure(lm=lm, adapter=BAMLAdapter())


class Entities(BaseModel):
    Company: list[str] | None = Field(
        None,
        description="Official or unofficial name of a registered company or a brand.",
    )
    Date: list[str] | None = Field(
        None,
        description='Specific time period, whether explicitly mentioned (e.g., "year ended March 2020") or implicitly referred to (e.g., "last month"), in the past, present, or future.',
    )
    Location: list[str] | None = Field(
        None,
        description="Represents geographical locations, such as political regions, countries, states, cities, roads, or any other location, even when used as adjectives.",
    )
    Money: list[str] | None = Field(
        None,
        description="Monetary value expressed in any world currency, including digital currencies.",
    )
    Person: list[str] | None = Field(
        None,
        description="Name of an individual.",
    )
    Product: list[str] | None = Field(
        None,
        description="Any physical object or service manufactured or provided by a company to consumers, excluding references to businesses or sectors within the financial context.",
    )
    Quantity: list[str] | None = Field(
        None,
        description="Any numeric value that is not categorized as Money, such as percentages, numbers, measurements (e.g., weight, length), or other similar quantities. Note that unit of measurements are also part of the entity.",
    )


class FinancialEntitiesInfo(dspy.Signature):
    """
    Identify and extract entities from the following financial news text into the following categories:
    - Extract all relevant entities as a list of strings, preserving the wording from the text
    - Use None if no entities are found in that category
    - Only extract entities that are explicitly mentioned in the text itself, do not make inferences or reason about what entities might be implied based on URLs, domain names, or other indirect references
    - Extract individual items rather than compound or ranged entities (e.g., if a range or compound entity is mentioned, extract each individual item separately)
    """

    text: str = dspy.InputField()
    entities: Entities = dspy.OutputField()


class ExtractFinancialEntities(dspy.Module):
    def __init__(self) -> None:
        self.extract_entities = dspy.Predict(FinancialEntitiesInfo)

    async def aforward(self, record: dict[str, Any]) -> dict[str, Any]:
        result = await self.extract_entities.acall(text=record["text"])
        output = result.entities.model_dump(mode="json")
        output["record_id"] = record["record_id"]
        return output

    def forward(self, record: dict[str, Any]) -> dict[str, Any]:
        result = self.extract_entities(text=record["text"])
        output = result.entities.model_dump(mode="json")
        output["record_id"] = record["record_id"]
        return output


async def extract_entities_async(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract financial entities from multiple records concurrently."""

    extractor = ExtractFinancialEntities()

    async def extract_single_record(record: dict[str, Any]) -> dict[str, Any]:
        extracted_data = await extractor.aforward(record)
        print(f"Record {record['record_id']} completed")
        return extracted_data

    tasks = [extract_single_record(record) for record in records]
    results = await asyncio.gather(*tasks)
    sorted_results = sorted(results, key=lambda x: x["record_id"])
    return sorted_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", "-s", type=int, default=1, help="Start index")
    parser.add_argument("--end", "-e", type=int, default=100, help="End index")
    parser.add_argument(
        "--fname",
        "-f",
        type=str,
        default="../data/financial_ner.parquet",
        help="Input file name",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="../data/structured_output_dspy.json",
        help="Output file name",
    )
    args = parser.parse_args()
    if args.start < 1 or args.start > args.end:
        raise ValueError("Start index must be 1 or greater and <= end index.")

    df = pl.read_parquet(args.fname)
    df = df.with_row_index("record_id", offset=1)
    records = df.to_dicts()
    records = records[args.start - 1 : args.end]

    print(f"Processing {len(records)} records...")
    extracted_results = asyncio.run(extract_entities_async(records))
    with open(args.output, "w") as f:
        for record in extracted_results:
            f.write(f"{json.dumps(record)}\n")
    print(f"\nCompleted processing {len(extracted_results)} records and saved to {args.output}")
