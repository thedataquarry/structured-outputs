"""
Run a BAML pipeline to extract information from the FHIR unstructured patient notes data
and outputs the results to newline-delimited JSON files.
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


async def extract_patient(record: Dict[str, str]) -> Dict[str, Any]:
    async with api_semaphore:
        await asyncio.sleep(REQUEST_DELAY)
        patient = await b.ExtractPatient(record["note"])
        output = patient.model_dump()
        # Clean up output
        output["record_id"] = record["record_id"]
        output["maritalStatus"] = output["maritalStatus"].value if output["maritalStatus"] else None
        print(f"✓ Extracted patient details for record {record['record_id']}")
        return output


async def extract_practitioner(record: Dict[str, str]) -> List[Dict[str, Any]]:
    async with api_semaphore:
        await asyncio.sleep(REQUEST_DELAY)
        practitioners = await b.ExtractPractitioner(record["note"])
        output = [item.model_dump() for item in practitioners]
        print(f"✓ Extracted practitioner details for record {record['record_id']}")
        return output


async def extract_immunization(record: Dict[str, str]) -> List[Dict[str, Any]]:
    async with api_semaphore:
        await asyncio.sleep(REQUEST_DELAY)
        immunization = await b.ExtractImmunization(record["note"])
        output = [i.model_dump() for i in immunization]
        # Add record_id to each immunization entry for safety
        for item in output:
            item["record_id"] = record["record_id"]
        print(f"✓ Extracted immunization for record {record['record_id']}")
        return output


async def process_record(record: Dict[str, str]) -> Dict[str, Any]:
    # Run all extractions concurrently for the same record
    tasks = [
        extract_patient(record),
        extract_practitioner(record),
        extract_immunization(record),
    ]

    try:
        patient_result, practitioner_result, immunization_result = await asyncio.gather(*tasks)

        # Create the desired JSON structure
        result = {
            "patient": patient_result,
            "practitioner": practitioner_result
            if practitioner_result
            and not all(all(v is None for v in item.values()) for item in practitioner_result)
            else None,
            "immunization": immunization_result
            if not all(v is None for v in immunization_result)
            else None,
        }

        return result
    except Exception as e:
        print(f"❌ Error processing record {record['record_id']}: {e}")
        # Return basic structure with record_id on error
        return {
            "patient": {"record_id": record["record_id"], "error": str(e)},
            "practitioner": None,
            "immunization": None,
        }


async def extract(records: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    print(f"Processing {len(records)} records")
    tasks = [process_record(record) for record in records]
    results = await asyncio.gather(*tasks)
    return results


async def main(fname: str, start: int, end: int) -> None:
    "Run the information extraction workflow"
    df = pl.read_json(fname)
    records = df.to_dicts()
    records = records[start - 1 : end]

    results = await extract(records)
    # Sort results by record_id to ensure consistent ordering
    results = sorted(results, key=lambda x: x["patient"]["record_id"])
    # Write out the results
    results_df = pl.DataFrame(results)
    results_df.write_ndjson(args.output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--start", "-s", type=int, default=1, help="Start index")
    parser.add_argument("--end", "-e", type=int, default=10, help="End index")
    parser.add_argument(
        "--fname",
        "-f",
        type=str,
        default="../data/note.json",
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
