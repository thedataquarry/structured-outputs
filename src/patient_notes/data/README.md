# Patient notes

Field | Description
--- | ---
Source URL | FHIR patient records from [Hugging Face datasets](https://huggingface.co/datasets/kishanbodybrain/test-fhir/tree/main/data)
Input format | Plain text
Output format | Nested JSON
Number of records | 2,726

The raw data from the source is in parquet files are transformed into JSON. This raw JSON file of FHIR healthcare records
(`data/raw_fhir.json`) serves as our source of truth for evaluating the structured output performance
from either approach.

## Unstructured data

The patient notes (unstructured data) we will be using for our structured output task is in
`note.json`. It contains a patient record as unstructured text, 

## Evaluation data

The evaluation data is in [FHIR](https://build.fhir.org/formats.html) format, a standardized
format used in the US healthcare system. It's very deeply nested, so for making the
structured output task and evaluation more feasible, a transformation script is provided, that
runs on the `raw_fhir.json` file that contains the gold data in FHIR format.

```bash
uv run transform_fhir.py
```

Running this script will ouput the file `gold.json`, which contains the gold data for the fields we want to extract from the unstructured text. This file is used for evaluation.