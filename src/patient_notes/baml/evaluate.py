import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add a mapping of state abbreviations to full state names
STATE_ABBR_TO_NAME = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}


def load_and_match_records(gold_path: Path, result_path: Path) -> List[Tuple[Dict, Dict]]:
    """Load JSON files and match records by record_id."""
    with open(gold_path, "r") as f:
        gold_data = json.load(f)

    with open(result_path, "r") as f:
        result_data = [json.loads(line.strip()) for line in f if line.strip()]

    # Create lookup for result data by patient.record_id
    result_lookup = {}
    for item in result_data:
        if "patient" in item and "record_id" in item["patient"]:
            result_lookup[item["patient"]["record_id"]] = item

    # Match records by record_id
    matched_pairs = []
    for gold_record in gold_data:
        gold_id = gold_record["record_id"]
        if gold_id in result_lookup:
            matched_pairs.append((gold_record, result_lookup[gold_id]))

    return matched_pairs


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


def safe_get_nested(data: Dict, path: str, default=None) -> Any:
    """Safely get nested dictionary value using dot notation."""
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def normalize_state(state_val: Any) -> str | None:
    """Normalize state value to full state name."""
    if state_val is None:
        return None

    state_str = str(state_val).strip()
    if not state_str:
        return None

    # If it's already a full state name, return as-is (case normalized)
    state_upper = state_str.upper()
    if state_upper in STATE_ABBR_TO_NAME:
        return STATE_ABBR_TO_NAME[state_upper].lower()

    # Check if it matches a full state name (case-insensitive)
    state_lower = state_str.lower()
    for abbr, full_name in STATE_ABBR_TO_NAME.items():
        if full_name.lower() == state_lower:
            return full_name.lower()

    # Return original if no match found
    return state_lower


def extract_date_part(val: Any) -> str | None:
    """Extract date part from datetime string, ignoring time component."""
    if val is None:
        return None
    return str(val).split("T")[0].strip()


def normalize_date(val: Any) -> str | None:
    """Normalize date to ISO format (YYYY-MM-DD) from various formats."""
    if val is None:
        return None

    date_str = str(val).strip()
    if not date_str:
        return None

    # Extract date part if it contains time (split on 'T')
    date_str = date_str.split("T")[0].strip()

    # If already in ISO format (YYYY-MM-DD), return as-is
    if len(date_str) == 10 and date_str.count("-") == 2:
        parts = date_str.split("-")
        if len(parts) == 3 and parts[0].isdigit() and len(parts[0]) == 4:
            return date_str

    # Try to parse natural language format like "November 12, 1988"
    try:
        from datetime import datetime

        # Handle various formats
        for fmt in ["%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    except Exception:
        pass

    # Return original if no conversion possible
    return date_str


def compare_values(val1: Any, val2: Any, field_name: str = "") -> bool:
    """Compare two values for equality, handling None and different types."""
    if val1 is None and val2 is None:
        return True
    if val1 is None or val2 is None:
        return False

    # Special handling for state fields
    if "state" in field_name.lower():
        norm_val1 = normalize_state(val1)
        norm_val2 = normalize_state(val2)
        return norm_val1 == norm_val2

    # Special handling for date fields (birthDate, encounter periods)
    if "birthdate" in field_name.lower():
        # Use full date normalization for birth dates (handles natural language)
        date1 = normalize_date(val1)
        date2 = normalize_date(val2)
        return date1 == date2
    elif "encounter_period" in field_name.lower():
        # Use simple date extraction for encounter periods (datetime to date only)
        date1 = extract_date_part(val1)
        date2 = extract_date_part(val2)
        return date1 == date2

    # Handle array vs string for address lines (common in practitioner addresses)
    if isinstance(val1, list) and isinstance(val2, str):
        if len(val1) == 1:
            return val1[0].lower().strip() == val2.lower().strip()
        return False

    if isinstance(val2, list) and isinstance(val1, str):
        if len(val2) == 1:
            return val1.lower().strip() == val2[0].lower().strip()
        return False

    # Handle list comparison
    if isinstance(val1, list) and isinstance(val2, list):
        return val1 == val2

    # Handle string comparison (case-insensitive for addresses)
    return str(val1).lower().strip() == str(val2).lower().strip()


def evaluate_patient_fields(gold_record: Dict, result_record: Dict, counter: FieldCounter):
    """Evaluate patient-level fields."""
    result_patient = result_record.get("patient", {})
    record_id = gold_record.get("record_id")

    # Top-level patient fields
    patient_fields = [
        "gender",
        "phone",
        "email",
        "maritalStatus",
        "age",
        "birthDate",
    ]
    for field in patient_fields:
        gold_val = gold_record.get(field)
        result_val = result_patient.get(field)
        is_match = compare_values(gold_val, result_val, f"patient.{field}")
        counter.add_comparison(f"patient.{field}", is_match, record_id)

    # Name fields
    if "name" in gold_record or "name" in result_patient:
        gold_name = gold_record.get("name", {}) or {}
        result_name = result_patient.get("name", {}) or {}

        name_fields = ["family", "given", "prefix"]
        for field in name_fields:
            gold_val = gold_name.get(field) if gold_name else None
            result_val = result_name.get(field) if result_name else None
            is_match = compare_values(gold_val, result_val, f"patient.name.{field}")
            counter.add_comparison(f"patient.name.{field}", is_match, record_id)

    # Address fields
    if "address" in gold_record or "address" in result_patient:
        gold_addr = gold_record.get("address", {})
        result_addr = result_patient.get("address", {})

        if gold_addr is not None or result_addr is not None:
            addr_fields = ["line", "city", "state", "postalCode", "country"]
            for field in addr_fields:
                gold_val = gold_addr.get(field) if gold_addr else None
                result_val = result_addr.get(field) if result_addr else None
                is_match = compare_values(gold_val, result_val, f"patient.address.{field}")
                counter.add_comparison(f"patient.address.{field}", is_match, record_id)


def evaluate_practitioner_arrays(gold_record: Dict, result_record: Dict, counter: FieldCounter):
    """Evaluate practitioner arrays with null checks."""
    gold_practitioners = gold_record.get("practitioner")
    result_practitioners = result_record.get("practitioner")
    record_id = gold_record.get("record_id")

    # Only evaluate if both have practitioners (non-null, non-empty)
    if (
        gold_practitioners is not None
        and len(gold_practitioners) > 0
        and result_practitioners is not None
        and len(result_practitioners) > 0
    ):
        # Collect all address lines from all practitioners into sets for comparison
        def normalize_address_line(val):
            """Normalize address line for set comparison."""
            if val is None:
                return None
            if isinstance(val, list):
                if len(val) == 1:
                    return val[0].lower().strip() if val[0] else None
                return None  # Skip multi-element arrays for now
            return str(val).lower().strip()

        gold_address_lines = set()
        result_address_lines = set()

        for prac in gold_practitioners:
            addr = prac.get("address", {})
            if addr and addr.get("line"):
                normalized = normalize_address_line(addr["line"])
                if normalized:
                    gold_address_lines.add(normalized)

        for prac in result_practitioners:
            addr = prac.get("address", {})
            if addr and addr.get("line"):
                normalized = normalize_address_line(addr["line"])
                if normalized:
                    result_address_lines.add(normalized)

        # Compare address line sets
        address_lines_match = gold_address_lines == result_address_lines
        counter.add_comparison("practitioner.address.line", address_lines_match, record_id)

        # For other fields, use first practitioner comparison (simpler approach)
        gold_prac = gold_practitioners[0]
        result_prac = result_practitioners[0]

        # Name fields
        gold_name = gold_prac.get("name", {}) or {}
        result_name = result_prac.get("name", {}) or {}
        name_fields = ["family", "given", "prefix"]
        for field in name_fields:
            gold_val = gold_name.get(field) if gold_name else None
            result_val = result_name.get(field) if result_name else None
            is_match = compare_values(gold_val, result_val, f"practitioner.name.{field}")
            counter.add_comparison(f"practitioner.name.{field}", is_match, record_id)

        # Direct practitioner fields
        prac_fields = ["phone", "email"]
        for field in prac_fields:
            gold_val = gold_prac.get(field)
            result_val = result_prac.get(field)
            is_match = compare_values(gold_val, result_val, f"practitioner.{field}")
            counter.add_comparison(f"practitioner.{field}", is_match, record_id)

        # Other address fields (using first practitioner)
        gold_addr = gold_prac.get("address", {})
        result_addr = result_prac.get("address", {})
        if gold_addr is not None or result_addr is not None:
            addr_fields = ["city", "state", "postalCode", "country"]
            for field in addr_fields:
                gold_val = gold_addr.get(field) if gold_addr else None
                result_val = result_addr.get(field) if result_addr else None
                is_match = compare_values(gold_val, result_val, f"practitioner.address.{field}")
                counter.add_comparison(f"practitioner.address.{field}", is_match, record_id)


def evaluate_practitioner_count(gold_record: Dict, result_record: Dict, counter: FieldCounter):
    """Evaluate practitioner count matching."""
    gold_practitioners = gold_record.get("practitioner")
    result_practitioners = result_record.get("practitioner")
    record_id = gold_record.get("record_id")

    # Compare practitioner counts (handles null cases)
    gold_count = len(gold_practitioners) if gold_practitioners else 0
    result_count = len(result_practitioners) if result_practitioners else 0

    is_count_match = gold_count == result_count
    counter.add_comparison("practitioner.count", is_count_match, record_id)


def evaluate_immunization_arrays(gold_record: Dict, result_record: Dict, counter: FieldCounter):
    """Evaluate immunization arrays using count matching."""
    gold_immunizations = gold_record.get("immunization")
    result_immunizations = result_record.get("immunization")
    record_id = gold_record.get("record_id")

    # Compare immunization counts (handles null cases)
    gold_count = len(gold_immunizations) if gold_immunizations else 0
    result_count = len(result_immunizations) if result_immunizations else 0

    is_count_match = gold_count == result_count
    counter.add_comparison("immunization.count", is_count_match, record_id)


def evaluate_allergy_data(gold_record: Dict, result_record: Dict, counter: FieldCounter):
    """Evaluate allergy data handling structural differences."""
    gold_allergy = gold_record.get("allergy", {})
    result_allergy = result_record.get("patient", {}).get("allergy", [])
    record_id = gold_record.get("record_id")

    # Handle structural differences:
    # Gold: allergy.substance (array or null)
    # Result: patient.allergy (array of objects with substance arrays)

    gold_substances = []
    if gold_allergy and gold_allergy.get("substance"):
        gold_substances = gold_allergy["substance"]

    result_substances = []
    if result_allergy:
        for allergy_obj in result_allergy:
            if allergy_obj.get("substance"):
                result_substances.extend(allergy_obj["substance"])

    # Compare substance counts (handles null cases)
    gold_count = len(gold_substances)
    result_count = len(result_substances)

    is_count_match = gold_count == result_count
    counter.add_comparison("allergy.count", is_count_match, record_id)


def generate_evaluation_report(counter: FieldCounter) -> str:
    """Generate evaluation report with count/percentage format and mismatch record IDs."""
    results = counter.get_results()
    mismatches = counter.get_mismatches()

    if not results:
        return "No evaluation results found."

    report_lines = []
    report_lines.append("=== Field-Level Evaluation Results ===\n")

    # Group by category
    categories = {
        "Patient Fields": [k for k in results.keys() if k.startswith("patient.")],
        "Practitioner Fields": [
            k for k in results.keys() if k.startswith("practitioner.") and k != "practitioner.count"
        ],
        "Practitioner Count Fields": [k for k in results.keys() if k == "practitioner.count"],
        "Immunization Fields": [k for k in results.keys() if k.startswith("immunization.")],
        "Allergy Fields": [k for k in results.keys() if k.startswith("allergy.")],
    }

    for category, fields in categories.items():
        if fields:
            report_lines.append(f"{category}:")
            for field in sorted(fields):
                matches, total, percentage = results[field]
                mismatch_records = mismatches.get(field, [])

                line = f"  {field} -> {matches}/{total} ({percentage:.1f}%)"
                if mismatch_records:
                    line += f" [mismatches: {mismatch_records}]"
                report_lines.append(line)
            report_lines.append("")

    # Overall statistics
    total_matches = sum(matches for matches, _, _ in results.values())
    total_fields = sum(total for _, total, _ in results.values())
    overall_accuracy = (total_matches / total_fields * 100) if total_fields > 0 else 0.0

    report_lines.append("=== Overall Statistics ===")
    report_lines.append(f"Total Fields Evaluated: {total_fields}")
    report_lines.append(f"Total Matches: {total_matches}")
    report_lines.append(f"Overall Accuracy: {overall_accuracy:.1f}%")

    return "\n".join(report_lines)


def run_evaluation_pipeline(gold_path: Path, result_path: Path) -> str:
    """Main evaluation pipeline function."""
    # Load and match records
    matched_pairs = load_and_match_records(gold_path, result_path)
    print(f"Matched {len(matched_pairs)} records for evaluation")

    # Initialize field counter
    counter = FieldCounter()

    # Evaluate each matched pair
    for gold_record, result_record in matched_pairs:
        evaluate_patient_fields(gold_record, result_record, counter)
        evaluate_practitioner_count(gold_record, result_record, counter)
        evaluate_practitioner_arrays(gold_record, result_record, counter)
        evaluate_immunization_arrays(gold_record, result_record, counter)
        evaluate_allergy_data(gold_record, result_record, counter)

    # Generate and return report
    return generate_evaluation_report(counter)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate BAML extraction results")
    parser.add_argument(
        "--gold",
        "-g",
        type=str,
        default="../data/gold.json",
        help="Path to the gold standard file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="../data/structured_output_baml.json",
        help="Path to the results file",
    )
    args = parser.parse_args()

    gold_file = Path(args.gold)
    result_file = Path(args.output)

    report = run_evaluation_pipeline(gold_file, result_file)
    print(report)
