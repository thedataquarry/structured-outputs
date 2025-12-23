"""
Run a BAML pipeline to extract PII from unstructured text
and output the results to newline-delimited JSON files.
"""

import asyncio
import os
from typing import Any, Dict, List

import polars as pl
from dotenv import load_dotenv

os.environ["BAML_LOG"] = "WARN"

from baml_client.async_client import b

load_dotenv()

# Rate limiting configuration to avoid overwhelming the API (esp. for smaller/less popular models)
MAX_CONCURRENT_REQUESTS = 20  # Adjust based on the API limit
REQUEST_DELAY = 0.01  # Delay between individual API calls in seconds

# Global semaphore to limit concurrent API requests
api_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def extract_pii(record: Dict[str, Any]) -> Dict[str, Any]:
    async with api_semaphore:
        await asyncio.sleep(REQUEST_DELAY)
        pii = await b.ExtractPii(record["text"])
        output = pii.model_dump()
        output["record_id"] = record["record_id"]
        print(f"✓ Extracted PII for record {record['record_id']}")
        return output


async def process_record(record: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return await extract_pii(record)
    except Exception as e:
        print(f"❌ Error processing record {record['record_id']}: {e}")
        return {"record_id": record["record_id"], "error": str(e)}


async def extract(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    print(f"Processing {len(records)} records")
    tasks = [process_record(record) for record in records]
    results = await asyncio.gather(*tasks)
    return results


async def main(fname: str, start: int, end: int) -> None:
    "Run the information extraction workflow"
    df = pl.read_parquet(fname)
    df = df.with_row_index("record_id", offset=1)
    records = df.to_dicts()
    records = records[start - 1 : end]

    results = await extract(records)
    results = sorted(results, key=lambda x: x["record_id"])
    results_df = pl.DataFrame(results)
    results_df.write_ndjson(args.output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--start", "-s", type=int, default=1, help="Start index")
    parser.add_argument("--end", "-e", type=int, default=100, help="End index")
    parser.add_argument(
        "--fname",
        "-f",
        type=str,
        default="../data/pii.parquet",
        help="Input file name",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="../data/structured_output_baml.json",
        help="Output file name",
    )
    args = parser.parse_args()
    if args.start < 1:
        raise ValueError("Start index must be 1 or greater")

    asyncio.run(main(args.fname, start=args.start, end=args.end))
