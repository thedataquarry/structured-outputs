# Copyright Cleanlab.ai
# SPDX-License-Identifier: Apache-2.0
# This file has been modified from its original version to be less strict, so as to allow for partial extractions.
# Original code can be found here: https://github.com/cleanlab/structured-output-benchmark

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ClaimHeader(BaseModel):
    claim_id: str | None = Field(
        ..., description="Claim ID in format CLM-XXXXXX, where X is a digit"
    )
    report_date: date | None = Field(
        ..., description="Date claim was reported in YYYY-MM-DD format"
    )
    incident_date: date | None = Field(
        ..., description="Date incident occurred in YYYY-MM-DD format"
    )
    reported_by: str | None = Field(
        ..., min_length=1, description="Full name of person reporting claim"
    )
    channel: Literal["Email", "Phone", "Portal", "In-Person"] | None = Field(
        ..., description="Channel used to report claim"
    )


class PolicyDetails(BaseModel):
    policy_number: str | None = Field(
        ..., description="Policy number in format POL-XXXXXXXXX, where X is a digit"
    )
    policyholder_name: str | None = Field(
        ..., min_length=1, description="Full legal name on policy"
    )
    coverage_type: Literal["Property", "Auto", "Liability", "Health", "Travel", "Other"] | None = (
        Field(..., description="Type of insurance coverage")
    )
    effective_date: date | None = Field(
        ..., description="Policy effective start date in YYYY-MM-DD format"
    )
    expiration_date: date | None = Field(
        ..., description="Policy expiration end date in YYYY-MM-DD format"
    )


class InsuredObject(BaseModel):
    object_id: str | None = Field(
        ...,
        description="Unique identifier for insured object. For vehicles, use VIN format (e.g., VIN12345678901234567). For buildings, use PROP-XXXXXX format. For liability, use LIAB-XXXXXX format. For other objects, use OBJ-XXXXXX format, where X is a digit",
    )
    object_type: Literal["Vehicle", "Building", "Person", "Other"] = Field(
        ..., description="Type of insured object"
    )
    make_model: Optional[str] = Field(
        None,
        description="Make and model for vehicles (use standardtized manufacturer names and models), or building type for property",
    )
    year: Optional[int] = Field(None, description="Year for vehicles or year built for buildings")
    location_address: Optional[str] = Field(
        None,
        description="Full street address where object is located or originated from",
    )
    estimated_value: Optional[int] = Field(
        None, description="Estimated monetary value in USD without currency symbol"
    )


class IncidentDescription(BaseModel):
    incident_type: Literal[
        "rear_end_collision",
        "side_impact_collision",
        "head_on_collision",
        "parking_lot_collision",
        "house_fire",
        "kitchen_fire",
        "electrical_fire",
        "burst_pipe_flood",
        "storm_damage",
        "roof_leak",
        "slip_and_fall",
        "property_injury",
        "product_liability",
        "theft_burglary",
        "vandalism",
    ] = Field(..., description="Specific standardized incident type")

    location_type: Literal[
        "intersection",
        "highway",
        "parking_lot",
        "driveway",
        "residential_street",
        "residence_interior",
        "residence_exterior",
        "commercial_property",
        "public_property",
    ] = Field(..., description="Standardized location type where incident occurred")

    estimated_damage_amount: Optional[int] = Field(
        None, description="Estimated damage in USD without currency symbol"
    )
    police_report_number: Optional[str] = Field(
        None, description="Police report number if applicable"
    )


class InsuranceClaim(BaseModel):
    header: ClaimHeader = Field(..., description="Basic claim information")
    policy_details: Optional[PolicyDetails] = Field(
        None, description="Policy information if available"
    )
    insured_objects: Optional[List[InsuredObject]] = Field(
        None, description="List of insured objects involved, if applicable"
    )
    incident_description: IncidentDescription | None = Field(
        ..., description="Structured incident details"
    )