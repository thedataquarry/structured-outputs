# BAML for structured outputs

This section contains code for getting structured outputs using BAML.

## Usage

```bash
# Extract structured outputs for the first 100 patient notes
uv run extract.py -e 100
# Extract from all 2,726 patient notes
uv run extract.py
```

The results are saved to `data/structured_output_baml.json`.

## Evaluation

An evaluation script is provided to compare the extracted structured outputs against a gold standard.
The gold standard file is `data/gold.json`, and is obtained by processing the raw JSON data in FHIR
format and reformatting it to match the expected output structure from the DSPy script.

```bash
uv run evaluate.py
```

## Results

The numbers below represent
the percentage of total exact matches from the evaluation script, comparing the structured outputs
against the gold standard. For comparison, the results from DSPy using the BAML adapter
are also shown.

| Model | BAML | DSPy w/ JSON schema | DSPy w/ BAML Adapter |
|-------|---|-------------------:|-------------------:|
| `mistralai/ministral-14b-2512` | 95.7% | ❌ | ❌ |
| `google/gemini-2.0-flash-001` | 96.3% | 87.6% | 96.6%x |
| `google/gemini-3-flash-preview` | 96.3% | 93.1% | 95.1% |
| `openai/gpt-4.1` | **97.4%** | **95.6%** | **96.8%** |
| `openai/gpt-5.2` | 96.8% | 97.0% | 96.5% |

> [!NOTE]
> The ❌ marks indicate cases where there was a parsing error on at least one of the records.
> This happens with smaller, less capable models in DSPy -- this dataset is relatively challenging
> and has multiple up to 3 levels of nesting.

The reason this could be happening is that DSPy's prompts are more verbose than BAML's
(because of the structured prompts that it uses). As a result, BAML outperforms DSPy across the
board, even when DSPy is used with the `BAMLAdapter`. For smaller, less capable models
(like `mistralai/ministral-14b-2512`), BAML's more concise prompts (relative to DSPy's) help the
model better focus on the context, and BAML's parser downstream fixes issues with the nested JSON
output, allowing it to perform better than DSPy overall. These qualities of BAML are well-documented
in their blog post "[Your prompts are using 4x more tokens than you need](https://boundaryml.com/blog/type-definition-prompting-baml)".

### Example results

For the first 100 records of the dataset, the results for `google/gemini-2.0-flash-001` are shown below.

```
Matched 100 records for evaluation
=== Field-Level Evaluation Results ===

Patient Fields:
  patient.address.city -> 61/61 (100.0%)
  patient.address.country -> 61/61 (100.0%)
  patient.address.line -> 56/61 (91.8%) [mismatches: [39, 41, 75, 85, 90]]
  patient.address.postalCode -> 55/61 (90.2%) [mismatches: [8, 28, 33, 34, 39, 100]]
  patient.address.state -> 61/61 (100.0%)
  patient.age -> 100/100 (100.0%)
  patient.birthDate -> 100/100 (100.0%)
  patient.email -> 100/100 (100.0%)
  patient.gender -> 96/100 (96.0%) [mismatches: [44, 72, 79, 89]]
  patient.maritalStatus -> 98/100 (98.0%) [mismatches: [64, 100]]
  patient.name.family -> 98/100 (98.0%) [mismatches: [45, 97]]
  patient.name.given -> 100/100 (100.0%)
  patient.name.prefix -> 95/100 (95.0%) [mismatches: [13, 15, 28, 37, 80]]
  patient.phone -> 100/100 (100.0%)

Practitioner Fields:
  practitioner.address.city -> 15/16 (93.8%) [mismatches: [24]]
  practitioner.address.country -> 15/16 (93.8%) [mismatches: [24]]
  practitioner.address.line -> 22/36 (61.1%) [mismatches: [14, 20, 24, 25, 28, 29, 33, 44, 45, 47]]
  practitioner.address.postalCode -> 14/16 (87.5%) [mismatches: [24, 34]]
  practitioner.address.state -> 15/16 (93.8%) [mismatches: [24]]
  practitioner.email -> 36/36 (100.0%)
  practitioner.name.family -> 35/36 (97.2%) [mismatches: [27]]
  practitioner.name.given -> 35/36 (97.2%) [mismatches: [27]]
  practitioner.name.prefix -> 36/36 (100.0%)
  practitioner.phone -> 35/36 (97.2%) [mismatches: [52]]

Practitioner Count Fields:
  practitioner.count -> 95/100 (95.0%) [mismatches: [15, 23, 73, 91, 93]]

Immunization Fields:
  immunization.count -> 91/100 (91.0%) [mismatches: [11, 14, 17, 54, 59, 71, 77, 81, 92]]

Allergy Fields:
  allergy.count -> 100/100 (100.0%)

=== Overall Statistics ===
Total Fields Evaluated: 1785
Total Matches: 1725
Overall Accuracy: 96.6%
```