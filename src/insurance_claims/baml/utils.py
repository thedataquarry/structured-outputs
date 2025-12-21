# Copyright Cleanlab.ai
# SPDX-License-Identifier: Apache-2.0
# Original code can be found here: https://github.com/cleanlab/structured-output-benchmark

import json
import re
from collections import defaultdict
from itertools import combinations, permutations
from pathlib import Path
from typing import Any, Dict, List, Tuple

exact_match_fields = {
    "header.claim_id",
    "header.channel",
    "header.reported_by",
    "policy_details.policy_number",
    "policy_details.policyholder_name",
    "policy_details.coverage_type",
    "incident_description.incident_type",
    "incident_description.location_type",
    "incident_description.weather_conditions",
    "incident_description.police_report_number",
}

enum_fields = {
    "header.channel",
    "policy_details.coverage_type",
    "incident_description.incident_type",
    "incident_description.location_type",
    "insured_objects.object_type",
}

date_fields = {
    "header.report_date",
    "header.incident_date",
    "policy_details.effective_date",
    "policy_details.expiration_date",
}

numeric_fields = {
    "incident_description.estimated_damage_amount",
    "insured_objects.estimated_value",
    "insured_objects.year",
}


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


def normalize_claim_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize claim record keys to match evaluation expectations."""
    normalized = dict(record)
    if "policy" in normalized and "policy_details" not in normalized:
        normalized["policy_details"] = normalized["policy"]
    return normalized


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


def calculate_field_breakdown(pred_dict, true_dict):
    """
    Calculate field-level accuracy breakdown using detailed comparison logic.

    Args:
        pred_dict: Predicted response dictionary
        true_dict: Ground truth dictionary

    Returns:
        Dict[str, bool]: Field-level correctness mapping
    """
    comparison_result = _compare_claims_detailed(true_dict, pred_dict)
    return comparison_result["field_correctness"]


def _flatten_dict(d, parent_key="", sep="."):
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key for nested keys
        sep: Separator for nested keys

    Returns:
        Dict[str, Any]: Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _compare_claims_detailed(ground_truth, extracted):
    """
    Compare claims using field-by-field comparison logic.

    Args:
        ground_truth: Ground truth dictionary
        extracted: Extracted response dictionary

    Returns:
        Dict containing overall accuracy, field accuracies, and detailed breakdown
    """
    if extracted is None:
        return {
            "overall_accuracy": 0.0,
            "field_accuracies": {},
            "extraction_failed": True,
            "errors": ["Extraction failed completely"],
            "exact_matches": 0,
            "total_fields": 0,
            "field_correctness": {},
        }

    errors = []
    field_accuracies = {}
    field_correctness = {}
    exact_matches = 0
    total_fields = 0

    # Compare header fields
    header_results = _compare_section_detailed(
        ground_truth.get("header", {}), extracted.get("header", {}), "header", errors
    )
    field_accuracies["header"] = header_results["accuracy"]
    field_correctness.update(header_results["field_correctness"])
    exact_matches += header_results["exact_matches"]
    total_fields += header_results["total_fields"]

    # Compare policy details
    if ground_truth.get("policy_details"):
        policy_results = _compare_section_detailed(
            ground_truth.get("policy_details", {}),
            extracted.get("policy_details", {}),
            "policy_details",
            errors,
        )
        field_accuracies["policy_details"] = policy_results["accuracy"]
        field_correctness.update(policy_results["field_correctness"])
        exact_matches += policy_results["exact_matches"]
        total_fields += policy_results["total_fields"]
    else:
        if extracted.get("policy_details"):
            errors.append("policy_details: Extracted policy details when none should exist")
            field_accuracies["policy_details"] = 0.0
            # Mark all extracted policy detail fields as incorrect
            for field in extracted.get("policy_details", {}).keys():
                field_correctness[f"policy_details.{field}"] = False
        else:
            field_accuracies["policy_details"] = 1.0

    # Compare insured objects
    if ground_truth.get("insured_objects"):
        objects_results = _compare_insured_objects_detailed(
            ground_truth.get("insured_objects", []),
            extracted.get("insured_objects", []),
            errors,
        )
        field_accuracies["insured_objects"] = objects_results["accuracy"]
        field_correctness.update(objects_results["field_correctness"])
        exact_matches += objects_results["exact_matches"]
        total_fields += objects_results["total_fields"]
    else:
        if extracted.get("insured_objects"):
            errors.append("insured_objects: Extracted objects when none should exist")
            field_accuracies["insured_objects"] = 0.0
            # Mark all individual fields in extracted objects as incorrect
            for i, obj in enumerate(extracted.get("insured_objects", [])):
                for field in obj.keys():
                    field_correctness[f"insured_objects[{i}].{field}"] = False
        else:
            field_accuracies["insured_objects"] = 1.0

    # Compare incident description
    incident_results = _compare_section_detailed(
        ground_truth.get("incident_description", {}),
        extracted.get("incident_description", {}),
        "incident_description",
        errors,
    )
    field_accuracies["incident_description"] = incident_results["accuracy"]
    field_correctness.update(incident_results["field_correctness"])
    exact_matches += incident_results["exact_matches"]
    total_fields += incident_results["total_fields"]

    # Calculate overall accuracy
    overall_accuracy = exact_matches / total_fields if total_fields > 0 else 0.0

    return {
        "overall_accuracy": overall_accuracy,
        "field_accuracies": field_accuracies,
        "field_correctness": field_correctness,
        "extraction_failed": False,
        "errors": errors,
        "exact_matches": exact_matches,
        "total_fields": total_fields,
        "exact_match_rate": overall_accuracy,
    }


def _compare_section_detailed(ground_truth, extracted, section_name, errors):
    """Compare section with detailed field-by-field analysis."""
    field_correctness = {}

    if not ground_truth:
        return {
            "accuracy": 1.0 if not extracted else 0.0,
            "exact_matches": 0,
            "total_fields": 0,
            "field_correctness": field_correctness,
        }

    if not extracted:
        errors.append(f"{section_name}: Missing entire section")
        # Mark all fields as incorrect
        for field in ground_truth.keys():
            field_correctness[f"{section_name}.{field}"] = False
        return {
            "accuracy": 0.0,
            "exact_matches": 0,
            "total_fields": len(ground_truth),
            "field_correctness": field_correctness,
        }

    exact_matches = 0
    total_fields = len(ground_truth)

    for field, gt_value in ground_truth.items():
        field_path = f"{section_name}.{field}"
        extracted_value = extracted.get(field)

        is_correct = _values_match_detailed(gt_value, extracted_value, field_path)
        field_correctness[field_path] = is_correct

        if is_correct:
            exact_matches += 1
        else:
            errors.append(f"{field_path}: Expected '{gt_value}', got '{extracted_value}'")

    accuracy = exact_matches / total_fields if total_fields > 0 else 1.0
    return {
        "accuracy": accuracy,
        "exact_matches": exact_matches,
        "total_fields": total_fields,
        "field_correctness": field_correctness,
    }


def _compare_insured_objects_detailed(ground_truth, extracted, errors):
    """Compare insured objects with optimal matching to handle out-of-order lists."""
    field_correctness = {}

    if not ground_truth:
        return {
            "accuracy": 1.0 if not extracted else 0.0,
            "exact_matches": 0,
            "total_fields": 0,
            "field_correctness": field_correctness,
        }

    if not extracted:
        errors.append("insured_objects: Missing all insured objects")
        total_fields = sum(len(obj) for obj in ground_truth)
        # Mark all fields as incorrect
        for i, obj in enumerate(ground_truth):
            for field in obj.keys():
                field_correctness[f"insured_objects[{i}].{field}"] = False
        return {
            "accuracy": 0.0,
            "exact_matches": 0,
            "total_fields": total_fields,
            "field_correctness": field_correctness,
        }

    total_exact_matches = 0
    total_fields = sum(len(obj) for obj in ground_truth)

    # Track count mismatch but still process matches
    if len(ground_truth) != len(extracted):
        errors.append(
            f"insured_objects: Count mismatch - expected {len(ground_truth)}, got {len(extracted)}"
        )

    # Find optimal pairing between ground truth and extracted objects
    optimal_pairing = _find_optimal_object_pairing(ground_truth, extracted)

    # Process each ground truth object with its best match
    for gt_idx, ext_idx in enumerate(optimal_pairing):
        gt_obj = ground_truth[gt_idx]

        if ext_idx is not None:
            # Found matching object, compare fields
            ext_obj = extracted[ext_idx]
            obj_results = _compare_section_detailed(
                gt_obj, ext_obj, f"insured_objects[{gt_idx}]", errors
            )
            total_exact_matches += obj_results["exact_matches"]
            field_correctness.update(obj_results["field_correctness"])
        else:
            # No matching object found, mark all fields as incorrect
            for field in gt_obj.keys():
                field_correctness[f"insured_objects[{gt_idx}].{field}"] = False
            errors.append(f"insured_objects[{gt_idx}]: No suitable matching object found")

    # Check for extra extracted objects not used in optimal pairing
    used_extracted_indices = set(idx for idx in optimal_pairing if idx is not None)
    for ext_idx, ext_obj in enumerate(extracted):
        if ext_idx not in used_extracted_indices:
            ext_id = ext_obj.get("object_id", f"index_{ext_idx}")
            errors.append(
                f"insured_objects: Extra object with ID '{ext_id}' not matched in optimal pairing"
            )

    accuracy = total_exact_matches / total_fields if total_fields > 0 else 1.0
    return {
        "accuracy": accuracy,
        "exact_matches": total_exact_matches,
        "total_fields": total_fields,
        "field_correctness": field_correctness,
    }


def _find_optimal_object_pairing(ground_truth, extracted):
    """Find optimal pairing between ground truth and extracted objects to maximize field matches."""
    if not ground_truth or not extracted:
        return [None] * len(ground_truth)

    # Use exhaustive search to find optimal assignment (lists are small, max 3 elements)
    return _exhaustive_optimal_pairing(ground_truth, extracted)


def _exhaustive_optimal_pairing(ground_truth, extracted):
    """Find globally optimal pairing using exhaustive search for small lists."""
    n_gt = len(ground_truth)
    n_ext = len(extracted)

    best_score = -1
    best_pairing = [None] * n_gt

    # Try all possible partial assignments (0 to min(n_gt, n_ext) matches)
    max_assignments = min(n_gt, n_ext)

    for num_matched in range(max_assignments + 1):
        if num_matched == 0:
            # Try the empty assignment (no matches)
            score = 0.0  # No matches means score of 0
            if score >= best_score:  # Use >= to prefer fewer assignments when scores are equal
                best_score = score
                best_pairing = [None] * n_gt
            continue

        # Try all ways to choose which ground truth objects to match
        for gt_indices in combinations(range(n_gt), num_matched):
            # Try all ways to assign extracted objects to chosen ground truth objects
            for ext_indices in permutations(range(n_ext), num_matched):
                pairing = [None] * n_gt
                for i, gt_idx in enumerate(gt_indices):
                    pairing[gt_idx] = ext_indices[i]

                score = _calculate_pairing_score(ground_truth, extracted, pairing)
                if score > best_score:
                    best_score = score
                    best_pairing = pairing

    return best_pairing


def _calculate_pairing_score(ground_truth, extracted, pairing):
    """Calculate total score for a given pairing."""
    total_score = 0.0

    for gt_idx, ext_idx in enumerate(pairing):
        if ext_idx is not None:
            gt_obj = ground_truth[gt_idx]
            ext_obj = extracted[ext_idx]
            total_score += _calculate_object_similarity(gt_obj, ext_obj)

    return total_score


def _calculate_object_similarity(gt_obj, ext_obj):
    """Calculate similarity score between two objects based on matching fields."""
    if not gt_obj or not ext_obj:
        return 0.0

    matches = 0
    total_fields = len(gt_obj)

    for field, gt_value in gt_obj.items():
        ext_value = ext_obj.get(field)
        field_path = f"insured_objects.{field}"  # Placeholder path for comparison

        if _values_match_detailed(gt_value, ext_value, field_path):
            matches += 1

    return matches / total_fields if total_fields > 0 else 0.0


def _values_match_detailed(gt_value, extracted_value, field_path):
    """Check if values match using appropriate matching rules for the field type."""

    # Handle None values
    if gt_value is None and extracted_value is None:
        return True
    if gt_value is None or extracted_value is None:
        return False

    def _normalize_value(value):
        if isinstance(value, str):
            # Remove punctuation and normalize whitespace for string comparison
            return re.sub(r"[^\w\s]", "", value.strip().lower()).replace(" ", "")
        return str(value).strip()

    def _normalize_enum(value):
        value_str = str(value).strip().lower()
        value_str = re.sub(r"[-\s]+", "_", value_str)
        return value_str

    # Enum field matching (snake_case_lower)
    if field_path in enum_fields:
        return _normalize_enum(gt_value) == _normalize_enum(extracted_value)

    # String field matching
    if field_path in exact_match_fields:
        return _normalize_value(gt_value) == _normalize_value(extracted_value)

    # Date field matching
    if field_path in date_fields:
        return str(gt_value) == str(extracted_value)

    # Numeric field matching
    if field_path in numeric_fields:
        try:
            gt_num = float(gt_value)
            ext_num = float(extracted_value)
            return gt_num == ext_num

        except (ValueError, TypeError):
            return str(gt_value) == str(extracted_value)

    # Default: exact string match
    return _normalize_value(gt_value) == _normalize_value(extracted_value)
