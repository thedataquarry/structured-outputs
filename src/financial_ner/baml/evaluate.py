import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


class FieldCounter:
    """Track field match counts and totals for evaluation reporting."""

    def __init__(self) -> None:
        self.counters = defaultdict(lambda: [0, 0])  # [matches, total]

    def add_counts(self, field_name: str, matches: int, total: int) -> None:
        """Add match/total counts for a field."""
        self.counters[field_name][0] += matches
        self.counters[field_name][1] += total

    def get_results(self) -> Dict[str, Tuple[int, int, float]]:
        """Get results as {field_name: (matches, total, percentage)}."""
        results = {}
        for field_name, (matches, total) in self.counters.items():
            percentage = (matches / total * 100) if total > 0 else 0.0
            results[field_name] = (matches, total, percentage)
        return results


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
            result_lookup[record_id] = item

    matched_pairs = []
    for idx, gold_record in enumerate(gold_data, start=1):
        record_id = gold_record.get("record_id", idx)
        gold_record = dict(gold_record)
        gold_record["record_id"] = record_id
        if record_id in result_lookup:
            matched_pairs.append((gold_record, result_lookup[record_id]))

    return matched_pairs


def normalize_empty(value: Any) -> Any:
    """Treat empty lists as None for equivalence checks."""
    if isinstance(value, list) and len(value) == 0:
        return None
    return value


def calculate_field_counts(result_record: Dict[str, Any], gold_record: Dict[str, Any]) -> Dict[str, Tuple[int, int]]:
    """Calculate per-field match counts using unordered set intersections."""
    field_counts: Dict[str, Tuple[int, int]] = {}
    for field, gold_value in gold_record.items():
        if field == "record_id":
            continue
        result_value = result_record.get(field)
        gold_value = normalize_empty(gold_value)
        result_value = normalize_empty(result_value)

        if gold_value is None and result_value is None:
            field_counts[field] = (1, 1)
            continue

        gold_set = set(gold_value or [])
        result_set = set(result_value or [])
        matches = len(gold_set & result_set)
        total = len(gold_set)
        field_counts[field] = (matches, total)
    return field_counts


def generate_evaluation_report(counter: FieldCounter) -> str:
    """Generate evaluation report with count/percentage format."""
    results = counter.get_results()

    if not results:
        return "No evaluation results found."

    report_lines = []
    report_lines.append("=== Field-Level Evaluation Results ===\n")

    for field in sorted(results.keys()):
        matches, total, percentage = results[field]
        report_lines.append(f"  {field} -> {matches}/{total} ({percentage:.1f}%)")

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
        field_counts = calculate_field_counts(result_record, gold_record)
        for field, (matches, total) in field_counts.items():
            counter.add_counts(field, matches, total)

    return generate_evaluation_report(counter)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate financial NER extraction results")
    parser.add_argument(
        "--gold",
        "-g",
        type=str,
        default="../data/gold.json",
        help="Path to the gold standard JSON file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="../data/structured_output_baml.json",
        help="Path to the extraction results (newline-delimited JSON)",
    )
    args = parser.parse_args()

    gold_path = Path(args.gold)
    result_path = Path(args.output)

    report = run_evaluation_pipeline(gold_path, result_path)
    print(report)
