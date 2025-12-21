"""
FHIR Bundle to Result Format Transformation Script

Transforms complex nested FHIR Bundle data into simplified structured format
matching the target schema in result_test.json.
"""

import json
from typing import Any, Dict, List, Optional


def get_coding_value(coding_obj: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract value from FHIR coding object, prioritizing display over text."""
    if not coding_obj:
        return None

    # Try coding array first
    if "coding" in coding_obj and coding_obj["coding"]:
        return coding_obj["coding"][0].get("display")

    # Fallback to text
    return coding_obj.get("text")


def extract_phone(telecom_list: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """Extract phone number from telecom array."""
    if not telecom_list:
        return None

    for item in telecom_list:
        if item.get("system") == "phone":
            return item.get("value")
    return None


def extract_email(telecom_list: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """Extract email from telecom array."""
    if not telecom_list:
        return None

    for item in telecom_list:
        if item.get("system") == "email":
            return item.get("value")
    return None


def extract_language(
    communication_list: Optional[List[Dict[str, Any]]],
) -> Optional[str]:
    """Extract primary language from communication array."""
    if not communication_list:
        return None

    for comm in communication_list:
        if "language" in comm:
            return get_coding_value(comm["language"])
    return None


def extract_address(
    address_list: Optional[List[Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    """Extract and flatten address structure."""
    if not address_list:
        return None

    addr = address_list[0]  # Take first address
    return {
        "line": addr["line"][0] if addr.get("line") else None,
        "city": addr.get("city"),
        "state": addr.get("state"),
        "postalCode": addr.get("postalCode"),
        "country": addr.get("country"),
    }


def extract_name(name_list: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    """Extract name structure, preferring official use."""
    if not name_list:
        return None

    # Try to find official name first
    for name in name_list:
        if name.get("use") == "official":
            return {
                "family": name.get("family"),
                "given": name.get("given", []),
                "prefix": name["prefix"][0] if name.get("prefix") else None,
            }

    # Fallback to first name
    name = name_list[0]
    return {
        "family": name.get("family"),
        "given": name.get("given", []),
        "prefix": name["prefix"][0] if name.get("prefix") else None,
    }


def extract_allergies(allergy_resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract allergy information with proper structure."""
    if not allergy_resources:
        return {"substance": None}

    substances = []
    for allergy in allergy_resources:
        if not allergy.get("code"):
            # Handle allergy with no specific substance
            substances.append(
                {
                    "category": "other",
                    "name": "allergy intolerance",
                    "manifestation": None,
                }
            )
            continue

        # Extract substance info
        substance_name = get_coding_value(allergy["code"])
        if substance_name and "shellfish" in substance_name.lower():
            substance_name = "shellfish"

        category = allergy["category"][0] if allergy.get("category") else "other"

        # Extract manifestations
        manifestations = []
        if allergy.get("reaction"):
            for reaction in allergy["reaction"]:
                if reaction.get("manifestation"):
                    for manifest in reaction["manifestation"]:
                        manifest_text = get_coding_value(manifest)
                        if manifest_text:
                            manifestations.append(manifest_text.lower())

        manifestation_str = ", ".join(manifestations) if manifestations else None

        substances.append(
            {
                "category": category,
                "name": substance_name,
                "manifestation": manifestation_str,
            }
        )

    return {"substance": substances if substances else None}


def extract_immunization(
    immunization_resources: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract immunization information from all immunization resources."""
    if not immunization_resources:
        return []

    immunizations = []

    for immunization in immunization_resources:
        # Extract vaccine name/traits
        traits = []
        if immunization.get("vaccineCode"):
            vaccine_name = get_coding_value(immunization["vaccineCode"])
            if vaccine_name:
                traits.append(vaccine_name)

        # Extract status
        status = immunization.get("status")

        # Extract occurrence date - check both fields, return non-null value or None if both are null
        occurrence_date_time = immunization.get("occurrenceDateTime")
        occurrence_string = immunization.get("occurrenceString")
        occurrence_date = occurrence_date_time or occurrence_string

        # Create individual immunization object
        immunization_obj = {
            "traits": traits if traits else None,
            "status": status,
            "occurrenceDate": occurrence_date,
        }

        immunizations.append(immunization_obj)

    return immunizations


def extract_organization_address(
    organization: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Extract address from Organization resource."""
    if not organization:
        return None

    # Organizations may have address in different places
    org_address = organization.get("address")
    if org_address:
        return extract_address(org_address)

    return None


def parse_display_name(display_name: str) -> List[Dict[str, Any]]:
    """Parse display name like 'Dr. Cletus Paucek' into FHIR name format."""
    if not display_name:
        return []

    parts = display_name.strip().split()
    if not parts:
        return []

    # Extract prefix (Dr., Mrs., etc.)
    prefix = None
    given = []
    family = None

    if parts[0].endswith("."):
        prefix = parts[0]
        name_parts = parts[1:]
    else:
        name_parts = parts

    if name_parts:
        # Last part is family name, rest are given names
        if len(name_parts) == 1:
            family = name_parts[0]
        else:
            given = name_parts[:-1]
            family = name_parts[-1]

    name_obj = {
        "family": family,
        "given": given,
    }

    if prefix:
        name_obj["prefix"] = [prefix]

    return [name_obj]


def find_organization_address_by_id(
    org_id: str, organizations: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Find organization address by organization ID."""
    if not org_id or not organizations:
        return None

    for org in organizations:
        if org.get("id") == org_id:
            return extract_organization_address(org)

    return None


def find_practitioners_from_encounters_and_resources(
    encounters: List[Dict[str, Any]],
    practitioners: List[Dict[str, Any]],
    organizations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Find all relevant practitioners from encounters and standalone practitioner resources."""

    found_practitioners = []
    processed_ids = set()

    # First, process practitioners referenced in encounters
    if encounters:
        for encounter in encounters:
            # Extract organization reference from serviceProvider if present
            service_provider_address = None
            service_provider = encounter.get("serviceProvider")
            if service_provider and service_provider.get("reference"):
                service_ref = service_provider["reference"]
                if service_ref.startswith("Organization/"):
                    org_id = service_ref.split("/")[-1]
                    service_provider_address = find_organization_address_by_id(
                        org_id, organizations
                    )

                    # If no Organization resource found but we have a display name, create address from it
                    if not service_provider_address and service_provider.get("display"):
                        service_provider_address = {
                            "line": service_provider["display"],
                            "city": None,
                            "state": None,
                            "postalCode": None,
                            "country": None,
                        }

            # Extract encounter period information
            encounter_period = encounter.get("period", {})
            encounter_start = encounter_period.get("start") if encounter_period else None
            encounter_end = encounter_period.get("end") if encounter_period else None

            if not encounter.get("participant"):
                continue

            for participant in encounter["participant"]:
                if not participant.get("individual", {}).get("reference"):
                    continue

                prac_ref = participant["individual"]["reference"]
                if not prac_ref.startswith("Practitioner/"):
                    continue

                prac_id = prac_ref.split("/")[-1]
                participant_display = participant["individual"].get("display")

                # Skip if already processed this practitioner
                if prac_id in processed_ids:
                    continue

                # Find matching practitioner
                found_matching_practitioner = False
                for prac in practitioners:
                    if prac.get("id") == prac_id:
                        found_matching_practitioner = True
                        processed_ids.add(prac_id)
                        enhanced_prac = prac.copy()

                        # If practitioner name is null, create name from participant display
                        if not prac.get("name") and participant_display:
                            enhanced_prac["name"] = parse_display_name(participant_display)

                        # Add organization address if available and practitioner doesn't have address
                        if service_provider_address and not prac.get("address"):
                            enhanced_prac["address"] = [service_provider_address]

                        # Add encounter period information
                        enhanced_prac["encounter_period"] = {
                            "start": encounter_start,
                            "end": encounter_end,
                        }

                        found_practitioners.append(enhanced_prac)
                        break

                # If no matching Practitioner resource found but we have participant display, create one
                if not found_matching_practitioner and participant_display:
                    processed_ids.add(prac_id)
                    created_prac = {
                        "id": prac_id,
                        "name": parse_display_name(participant_display),
                        "telecom": None,
                        "address": [service_provider_address] if service_provider_address else None,
                        "encounter_period": {
                            "start": encounter_start,
                            "end": encounter_end,
                        },
                    }
                    found_practitioners.append(created_prac)

    # Second, add any standalone Practitioner resources that weren't referenced in encounters
    for prac in practitioners:
        prac_id = prac.get("id")
        if prac_id not in processed_ids:
            # This is a standalone practitioner not referenced from encounters
            enhanced_prac = prac.copy()

            # No encounter period for standalone practitioners
            enhanced_prac["encounter_period"] = None

            found_practitioners.append(enhanced_prac)

    return found_practitioners


def transform_bundle_to_record(bundle: Dict[str, Any], record_id: int) -> Dict[str, Any]:
    """Transform a single FHIR bundle into target record format."""

    # Group resources by type
    resources = {
        "Patient": [],
        "Practitioner": [],
        "Encounter": [],
        "Organization": [],
        "AllergyIntolerance": [],
        "Immunization": [],
    }

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        if resource_type in resources:
            resources[resource_type].append(resource)

    # Extract patient data (should be one patient per bundle)
    patient = resources["Patient"][0] if resources["Patient"] else {}

    # Find all relevant practitioners
    practitioners = find_practitioners_from_encounters_and_resources(
        resources["Encounter"], resources["Practitioner"], resources["Organization"]
    )

    marital_status = get_coding_value(patient.get("maritalStatus"))
    marital_status = marital_status.replace(" ", "") if marital_status else None

    # Build result record
    record = {
        "record_id": record_id,
        "name": extract_name(patient.get("name")),
        "age": None,  # Not available in source data
        "gender": patient.get("gender"),
        "birthDate": patient.get("birthDate"),
        "phone": extract_phone(patient.get("telecom")),
        "email": None,  # Patient email not in source
        "maritalStatus": marital_status,
        "primaryLanguage": extract_language(patient.get("communication")),
        "address": extract_address(patient.get("address")),
        "practitioner": [
            {
                "name": extract_name(prac.get("name")),
                "phone": None,  # Practitioner phone not available
                "email": extract_email(prac.get("telecom")),
                "address": (
                    prac["address"][0]
                    if prac.get("address")
                    and isinstance(prac["address"], list)
                    and isinstance(prac["address"][0], dict)
                    and "line" in prac["address"][0]
                    else extract_address(prac.get("address"))
                ),
                "encounter_period": prac.get("encounter_period"),
            }
            for prac in practitioners
        ]
        if practitioners
        else None,
        "allergy": extract_allergies(resources["AllergyIntolerance"]),
        "immunization": extract_immunization(resources["Immunization"]),
    }

    return record


def transform_fhir_to_result_format(input_file: str, output_file: str):
    """Main transformation function."""

    with open(input_file, "r", encoding="utf-8") as f:
        bundles = json.load(f)

    transformed_records = []

    for i, bundle in enumerate(bundles):
        record = transform_bundle_to_record(bundle, record_id=i + 1)
        transformed_records.append(record)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(transformed_records, f, indent=2, ensure_ascii=False)

    print(f"Transformation complete. Output written to {output_file}")


if __name__ == "__main__":
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(script_dir, "raw_fhir.json")
    gold_file = os.path.join(script_dir, "gold.json")
    transform_fhir_to_result_format(test_file, gold_file)
