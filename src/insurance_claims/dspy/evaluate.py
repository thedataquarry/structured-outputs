import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import polars as pl

from utils import calculate_field_breakdown, normalize_claim_record


def parse_ground_truth(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return ast.literal_eval(value)


def write_gold_json(parquet_path: Path, gold_path: Path) -> None:
    df = pl.read_parquet(parquet_path)
    df = df.with_row_index("record_id", offset=1)
    records: List[Dict[str, Any]] = []

    for row in df.select(["record_id", "ground_truth"]).to_dicts():
        gold_record = parse_ground_truth(row["ground_truth"])
        gold_record["record_id"] = row["record_id"]
        records.append(gold_record)

    gold_path.parent.mkdir(parents=True, exist_ok=True)
    with open(gold_path, "w") as f:
        json.dump(records, f, indent=2)


class FieldCounter:
    """Track field matches and totals for evaluation reporting."""

    def __init__(self):
        self.counters = defaultdict(lambda: [0, 0])  # [matches, total]
        self.mismatches = defaultdict(list)  # record_ids where field mismatched

    def add_comparison(self, field_name: str, is_match: bool, record_id: int | None = None):
        """Add a field comparison result."""
        self.counters[field_name][1] += 1  # total
        if is_match:
            self.counters[field_name][0] += 1  # matches
        elif record_id is not None and len(self.mismatches[field_name]) < 10:
            self.mismatches[field_name].append(record_id)

    def get_results(self) -> Dict[str, Tuple[int, int, float]]:
        """Get results as {field_name: (matches, total, percentage)}."""
        results = {}
        for field_name, (matches, total) in self.counters.items():
            percentage = (matches / total * 100) if total > 0 else 0.0
            results[field_name] = (matches, total, percentage)
        return results

    def get_mismatches(self) -> Dict[str, List[int]]:
        """Get mismatch record IDs for each field."""
        return dict(self.mismatches)


def load_and_match_records(gold_path: Path, result_path: Path) -> List[Tuple[Dict, Dict]]:
    """Load JSON files and match records by record_id."""
    with open(gold_path, "r") as f:
        gold_data = json.load(f)

    with open(result_path, "r") as f:
        result_data = [json.loads(line.strip()) for line in f if line.strip()]

    result_lookup = {}
    for item in result_data:
        record_id = item.get("record_id")
        if record_id is not None:
            result_lookup[record_id] = normalize_claim_record(item)

    matched_pairs = []
    for gold_record in gold_data:
        gold_id = gold_record.get("record_id")
        if gold_id in result_lookup:
            matched_pairs.append((normalize_claim_record(gold_record), result_lookup[gold_id]))

    return matched_pairs


def generate_evaluation_report(counter: FieldCounter) -> str:
    """Generate evaluation report with count/percentage format and mismatch record IDs."""
    results = counter.get_results()
    mismatches = counter.get_mismatches()

    if not results:
        return "No evaluation results found."

    report_lines = []
    report_lines.append("=== Field-Level Evaluation Results ===\n")

    for field in sorted(results.keys()):
        matches, total, percentage = results[field]
        mismatch_records = mismatches.get(field, [])

        line = f"  {field} -> {matches}/{total} ({percentage:.1f}%)"
        if mismatch_records:
            line += f" [mismatches: {mismatch_records}]"
        report_lines.append(line)

    total_matches = sum(matches for matches, _, _ in results.values())
    total_fields = sum(total for _, total, _ in results.values())
    overall_accuracy = (total_matches / total_fields * 100) if total_fields > 0 else 0.0

    report_lines.append("\n=== Overall Statistics ===")
    report_lines.append(f"Total Fields Evaluated: {total_fields}")
    report_lines.append(f"Total Matches: {total_matches}")
    report_lines.append(f"Overall Accuracy: {overall_accuracy:.1f}%")

    return "\n".join(report_lines)


def run_evaluation_pipeline(gold_path: Path, result_path: Path) -> str:
    """Main evaluation pipeline function."""
    matched_pairs = load_and_match_records(gold_path, result_path)
    print(f"Matched {len(matched_pairs)} records for evaluation")

    counter = FieldCounter()

    for gold_record, result_record in matched_pairs:
        field_correctness = calculate_field_breakdown(result_record, gold_record)
        record_id = gold_record.get("record_id")
        for field, is_match in field_correctness.items():
            counter.add_comparison(field, is_match, record_id)

    return generate_evaluation_report(counter)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate insurance claim extraction results")
    parser.add_argument(
        "--parquet",
        "-p",
        type=str,
        default="../data/insurance_claims_extraction.parquet",
        help="Path to the source parquet file containing ground truth data",
    )
    parser.add_argument(
        "--gold",
        "-g",
        type=str,
        default="../data/insurance_claims_gold.json",
        help="Path to the gold standard JSON file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="../data/structured_output_dspy.json",
        help="Path to the extraction results (newline-delimited JSON)",
    )
    parser.add_argument(
        "--refresh-gold",
        action="store_true",
        help="Regenerate the gold JSON file from the parquet source",
    )
    args = parser.parse_args()

    parquet_path = Path(args.parquet)
    gold_path = Path(args.gold)
    result_path = Path(args.output)

    if args.refresh_gold or not gold_path.exists():
        write_gold_json(parquet_path, gold_path)

    report = run_evaluation_pipeline(gold_path, result_path)
    print(report)
