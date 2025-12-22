"""
Run a DSPy pipeline to extract information from unstructured insurance claims
and output the results to newline-delimited JSON files.
"""

import argparse
import asyncio
import json
import os
from typing import Any

import dspy
import polars as pl
from dotenv import load_dotenv
from dspy.adapters.baml_adapter import BAMLAdapter  # noqa: E402

from schema import InsuranceClaim

load_dotenv()

# Using OpenRouter. Switch to another LLM provider as needed
lm = dspy.LM(
    model="openrouter/google/gemini-3-flash-preview",
    api_base="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    cache=False,
)
dspy.configure(lm=lm, adapter=BAMLAdapter())


class InsuranceClaimInfo(dspy.Signature):
    """
    Extract the insurance claim information from the following text.
    - If you are unsure about a field, leave it as null.
    """

    claim_text: str = dspy.InputField()
    claim: InsuranceClaim = dspy.OutputField()


class ExtractClaim(dspy.Module):
    def __init__(self):
        self.extract_claim = dspy.Predict(InsuranceClaimInfo)

    async def aforward(self, record: dict[str, Any]) -> dict[str, Any]:
        result = await self.extract_claim.acall(claim_text=record["claim_text"])
        claim = result.claim.model_dump(mode="json")
        claim["record_id"] = record["record_id"]
        return claim

    def forward(self, record: dict[str, Any]) -> dict[str, Any]:
        result = self.extract_claim(claim_text=record["claim_text"])
        claim = result.claim.model_dump(mode="json")
        claim["record_id"] = record["record_id"]
        return claim


async def extract_claims_async(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract insurance claim information from multiple records concurrently."""

    extract_claim = ExtractClaim()

    async def extract_single_record(record: dict[str, Any]) -> dict[str, Any]:
        extracted_data = await extract_claim.aforward(record)
        print(f"Record {record['record_id']} completed")
        return extracted_data

    tasks = [extract_single_record(record) for record in records]
    results = await asyncio.gather(*tasks)
    sorted_results = sorted(results, key=lambda x: x["record_id"])
    return sorted_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", "-s", type=int, default=1, help="Start index")
    parser.add_argument("--end", "-e", type=int, default=50, help="End index")
    parser.add_argument(
        "--fname",
        "-f",
        type=str,
        default="../data/insurance_claims_extraction.parquet",
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
    extracted_results = asyncio.run(extract_claims_async(records))
    with open(args.output, "w") as f:
        for record in extracted_results:
            f.write(f"{json.dumps(record)}\n")
    print(f"\nCompleted processing {len(extracted_results)} records and saved to {args.output}")
