"""
Run a DSPy pipeline to extract information from the FHIR unstructured patient notes data
and outputs the results to newline-delimited JSON files.
"""

import argparse
import asyncio
import json
import os
from typing import Any, Literal

import dspy
import polars as pl
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from baml_adapter import BAMLAdapter

load_dotenv()

# Using OpenRouter. Switch to another LLM provider as needed
lm = dspy.LM(
    model="openrouter/google/gemini-2.0-flash-001",
    api_base="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    max_tokens=10_000,  # Max output tokens
)
dspy.configure(lm=lm, adapter=BAMLAdapter())


class PatientNote(BaseModel):
    record_id: int
    note: str


class PersonNameAndTitle(BaseModel):
    family: str | None = Field(default=None, description="surname")
    given: list[str] | None = Field(
        default=None,
        description="Given names (first and middle names)",
    )
    prefix: str | None = Field(
        default=None, description="title of the person, e.g., Dr., Mr., Mrs., Ms."
    )


class Address(BaseModel):
    line: str | None = Field(default=None, alias="street")
    city: str | None
    state: str | None
    postalCode: str | None
    country: Literal["US"] | None


class Practitioner(BaseModel):
    name: PersonNameAndTitle | None
    phone: str | None = Field(default=None, description="Phone number of the healthcare provider")
    email: str | None = Field(default=None, description="Email address of the healthcare provider")
    address: Address | None = Field(default=None, description="Address of the healthcare provider")


class Immunization(BaseModel):
    traits: list[str] | None = Field(
        default=None,
        description="Text describing the name and traits of the immunization",
    )
    status: Literal["completed"] | None = Field(
        default=None,
        description="If no traits are present, then the status cannot be determined",
    )
    occurrenceDate: str | None = Field(default=None, description="ISO-8601 format for date")


class Substance(BaseModel):
    category: Literal["environment", "food", "medication", "other"]
    name: str | None
    manifestation: str | None = Field(
        default=None,
        description="Text describing the manifestation of the allergy or intolerance",
    )


class Allergy(BaseModel):
    substance: list[Substance] = Field(description="Substances the patient is allergic to")


class Patient(BaseModel):
    record_id: int | None = Field(default=None)
    name: PersonNameAndTitle | None
    age: int | None
    gender: Literal["male", "female"] | None
    birthDate: str | None = Field(default=None, description="ISO-8601 format for date")
    phone: str | None = Field(default=None, description="Phone number of the patient")
    email: str | None = Field(default=None, description="Email address of the patient")
    maritalStatus: Literal["Married", "Divorced", "Widowed", "NeverMarried"] | None
    address: Address | None = Field(default=None, description="Residence address of the patient")
    allergy: list[Allergy] | None = Field(default=None)


class PatientInfo(dspy.Signature):
    """
    - Do not infer any information that is not explicitly mentioned in the text.
    - If you are unsure about any field, leave it as None.
    """

    note: PatientNote = dspy.InputField()
    patient: Patient = dspy.OutputField()


class PractitionerInfo(dspy.Signature):
    """
    - Do not infer any information that is not explicitly mentioned in the text.
    - If you are unsure about any field, leave it as None.
    """

    note: PatientNote = dspy.InputField()
    practitioner: list[Practitioner] | None = dspy.OutputField()


class ImmunizationInfo(dspy.Signature):
    """
    Extracts immunization information from a patient note.
    """

    note: PatientNote = dspy.InputField(desc="Immunization info only")
    immunization: list[Immunization] | None = dspy.OutputField()


class ExtractData(dspy.Module):
    def __init__(self):
        self.extract_patient = dspy.Predict(PatientInfo)
        self.extract_practitioner = dspy.Predict(PractitionerInfo)
        self.extract_immunization = dspy.Predict(ImmunizationInfo)

    async def aforward(
        self,
        note: dict[str, Any],
    ) -> dict[str, Any]:
        # Run all extractions concurrently
        r1, r2, r3 = await asyncio.gather(
            self.extract_patient.acall(note=note["note"]),
            self.extract_practitioner.acall(note=note["note"]),
            self.extract_immunization.acall(note=note["note"]),
        )

        # Process results
        r1.patient.record_id = note["record_id"]
        r1 = r1.patient.model_dump()
        r2 = [item.model_dump() for item in r2.practitioner] if r2.practitioner else None
        r3 = [item.model_dump() for item in r3.immunization] if r3.immunization else None
        # Combine the results into a dictionary
        result = {"patient": r1, "practitioner": r2, "immunization": r3}
        return result

    def forward(
        self,
        note: dict[str, Any],
    ) -> dict[str, Any]:
        # Append record_id to the result
        r1 = self.extract_patient(note=note["note"])
        r1.patient.record_id = note["record_id"]
        r1 = r1.patient.model_dump()

        r2 = self.extract_practitioner(note=note["note"])
        r2 = [item.model_dump() for item in r2.practitioner] if r2.practitioner else None
        r3 = self.extract_immunization(note=note["note"])
        r3 = [item.model_dump() for item in r3.immunization] if r3.immunization else None
        # Combine the results into a dictionary
        result = {"patient": r1, "practitioner": r2, "immunization": r3}
        return result


async def extract_patients_async(notes: list[dict[str, Any]]) -> list[dict]:
    """Extract patient information from multiple notes concurrently"""

    # Instantiate ExtractData
    extract_patient = ExtractData()

    async def extract_single_note(note: dict[str, Any]) -> dict:
        extracted_data = await extract_patient.aforward(note=note)
        print(f"✓ Record {note['record_id']} completed")
        return extracted_data

    # Create tasks for concurrent execution
    tasks = [extract_single_note(note) for note in notes]
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks)
    # Sort results by record_id in ascending order
    sorted_results = sorted(results, key=lambda x: x["patient"]["record_id"])

    return sorted_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", "-s", type=int, default=1, help="Start index")
    parser.add_argument("--end", "-e", type=int, default=10_000, help="End index")
    parser.add_argument(
        "--fname",
        "-f",
        type=str,
        default="../data/note.json",
        help="Input file name",
    )
    parser.add_argument(
        "--output_file",
        "-o",
        type=str,
        default="../data/structured_output_dspy.json",
        help="Output file name",
    )
    args = parser.parse_args()
    if args.start < 1 or args.start > args.end:
        raise ValueError("Start index must be greater than 1 and less than or equal to end index.")

    # Collect input data
    df = pl.read_json(args.fname)
    notes = df.to_dicts()
    notes = notes[args.start - 1 : args.end]  # Adjust for zero-based indexing

    # # Debug
    # extract_patient = ExtractData()
    # for note in notes:
    #     print(extract_patient(note))
    #     print(dspy.inspect_history(n=3))

    print(f"Processing {len(notes)} notes...")
    # Run async extraction
    extracted_results = asyncio.run(extract_patients_async(notes))
    # Write results to file
    with open(args.output_file, "w") as f:
        for i, (note, patient_info) in enumerate(zip(notes, extracted_results)):
            f.write(f"{json.dumps(patient_info)}\n")
    print(f"\nCompleted processing {len(extracted_results)} notes and saved to {args.output_file}")
