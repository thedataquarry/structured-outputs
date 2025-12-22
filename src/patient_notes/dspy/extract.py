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
from dspy.adapters.baml_adapter import BAMLAdapter
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# Using OpenRouter. Switch to another LLM provider as needed
lm = dspy.LM(
    model="openrouter/google/gemini-2.0-flash-001",
    api_base="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    cache=False,
)
dspy.configure(lm=lm, adapter=BAMLAdapter())


class PatientNote(BaseModel):
    record_id: int
    note: str


class PersonNameAndTitle(BaseModel):
    family: str | None = Field(default=None, description="Surname of the patient")
    given: list[str] | None = Field(
        default=None,
        description="Given name(s) of the patient",
    )
    prefix: str | None = Field(
        default=None, description="Title of the patient"
    )


class Address(BaseModel):
    line: str | None
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
        description="Text describing the name and traits of the immunization",
    )
    substances: list[str] | None = Field(
        description="Substances or vaccine components mentioned in the immunization",
    )
    status: Literal["completed"] | None
    occurrenceDate: str | None = Field(description="ISO-8601 format for datetime including timezone")


class Substance(BaseModel):
    category: Literal["environment", "food", "medication", "other"]
    name: str | None
    manifestation: str | None = Field(
        description="Text describing the manifestation of the allergy or intolerance",
    )


class Allergy(BaseModel):
    substance: list[Substance] | None = Field(description="The substance that the patient is allergic to")


class Patient(BaseModel):
    record_id: int | None = Field(default=None)
    name: PersonNameAndTitle | None
    age: int | None
    gender: Literal["male", "female"] | None
    birthDate: str | None = Field(description="Date of birth of the patient in ISO-8601 format")
    address: Address | None = Field(description="Residence address of the patient")
    phone: str | None = Field(default=None, description="Phone number of the patient")
    email: str | None = Field(default=None, description="Phone number of the patient")
    maritalStatus: Literal["Married", "Divorced", "Widowed", "NeverMarried"] | None
    primarLanguage: Literal["English", "Spanish"] | None
    allergy: list[Allergy] | None


class PatientRecord(BaseModel):
    patient: Patient | None
    practitioner: list[Practitioner] | None
    immunization: list[Immunization] | None


class PatientRecordInfo(dspy.Signature):
    """
    Extract patient, practitioner, and immunization information from the given note.
    - Do not infer any information that is not explicitly mentioned in the text.
    - If you are unsure about any field, leave it as None.
    """

    note: PatientNote = dspy.InputField()
    patient_record: PatientRecord = dspy.OutputField()


class ExtractData(dspy.Module):
    def __init__(self):
        self.extract_patient_record = dspy.Predict(PatientRecordInfo)

    async def aforward(
        self,
        note: dict[str, Any],
    ) -> dict[str, Any]:
        record = await self.extract_patient_record.acall(note=note["note"])
        patient_record = record.patient_record
        if patient_record and patient_record.patient:
            patient_record.patient.record_id = note["record_id"]
        result = patient_record.model_dump() if patient_record else {}
        result.setdefault("patient", {"record_id": note["record_id"]})
        return result

    def forward(
        self,
        note: dict[str, Any],
    ) -> dict[str, Any]:
        record = self.extract_patient_record(note=note["note"])
        patient_record = record.patient_record
        if patient_record and patient_record.patient:
            patient_record.patient.record_id = note["record_id"]
        result = patient_record.model_dump() if patient_record else {}
        result.setdefault("patient", {"record_id": note["record_id"]})
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
    parser.add_argument("--end", "-e", type=int, default=100, help="End index")
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
