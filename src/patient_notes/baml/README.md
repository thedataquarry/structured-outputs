# BAML for structured outputs

This section contains code for getting structured outputs using BAML.

## Usage

```bash
# Extract structured outputs for the first 200 patient notes
uv run extract.py -e 200
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
| `google/gemma-3-27b-it` | 90.9% | 88.9% | 94.4% |
| `google/gemini-2.0-flash-001` | 94.7% | 90.2% | 95.5% |
| `openai/gpt-4.1-nano`| 83.7% | 83.5% | 84.2% |
| `openai/gpt-4.1-mini`| 95.6% | 94.7% | 94.2% |
| `google/gemini-2.5-flash` | 95.3% | 90.6% | 95.5% |

BAML performs better than DSPy (default, which uses JSON schema). However, when we pass
use the `BAMLAdapter` in DSPy to pass in the BAML schema format to DSPy's generated prompt,
we see DSPy's performance on par with BAML's on most counts.

### Example results

For the first 200 records of the dataset, the results for `google/gemini-2.0-flash-001` are shown below.

```
Matched 199 records for evaluation
=== Field-Level Evaluation Results ===

Patient Fields:
  patient.address.city -> 115/119 (96.6%) [mismatches: [24, 129, 172, 197]]
  patient.address.country -> 115/119 (96.6%) [mismatches: [24, 129, 172, 197]]
  patient.address.line -> 106/119 (89.1%) [mismatches: [24, 39, 41, 75, 85, 90, 103, 115, 129, 149]]
  patient.address.postalCode -> 105/119 (88.2%) [mismatches: [8, 24, 28, 33, 34, 39, 100, 116, 129, 141]]
  patient.address.state -> 115/119 (96.6%) [mismatches: [24, 129, 172, 197]]
  patient.age -> 198/199 (99.5%) [mismatches: [182]]
  patient.birthDate -> 198/199 (99.5%) [mismatches: [179]]
  patient.email -> 199/199 (100.0%)
  patient.gender -> 179/199 (89.9%) [mismatches: [20, 22, 39, 41, 44, 49, 56, 58, 89, 102]]
  patient.maritalStatus -> 197/199 (99.0%) [mismatches: [103, 182]]
  patient.name.family -> 197/199 (99.0%) [mismatches: [45, 97]]
  patient.name.given -> 198/199 (99.5%) [mismatches: [129]]
  patient.name.prefix -> 188/199 (94.5%) [mismatches: [13, 15, 28, 37, 80, 106, 123, 126, 141, 145]]
  patient.phone -> 192/199 (96.5%) [mismatches: [28, 39, 52, 73, 83, 126, 163]]

Practitioner Fields:
  practitioner.address.city -> 32/36 (88.9%) [mismatches: [24, 129, 150, 166]]
  practitioner.address.country -> 32/36 (88.9%) [mismatches: [24, 129, 150, 166]]
  practitioner.address.line -> 47/71 (66.2%) [mismatches: [14, 20, 24, 25, 28, 29, 33, 44, 45, 47]]
  practitioner.address.postalCode -> 29/36 (80.6%) [mismatches: [24, 34, 63, 129, 138, 150, 166]]
  practitioner.address.state -> 32/36 (88.9%) [mismatches: [24, 129, 150, 166]]
  practitioner.email -> 70/71 (98.6%) [mismatches: [138]]
  practitioner.name.family -> 65/71 (91.5%) [mismatches: [15, 25, 27, 108, 138, 166]]
  practitioner.name.given -> 66/71 (93.0%) [mismatches: [15, 25, 27, 138, 166]]
  practitioner.name.prefix -> 67/71 (94.4%) [mismatches: [15, 25, 138, 166]]
  practitioner.phone -> 69/71 (97.2%) [mismatches: [52, 166]]

Practitioner Count Fields:
  practitioner.count -> 185/199 (93.0%) [mismatches: [23, 25, 66, 73, 77, 91, 93, 129, 150, 168]]

Immunization Fields:
  immunization.count -> 177/199 (88.9%) [mismatches: [7, 14, 17, 18, 27, 29, 30, 51, 59, 70]]

Allergy Fields:
  allergy.count -> 191/199 (96.0%) [mismatches: [68, 108, 151, 159, 166, 167, 184, 195]]

=== Overall Statistics ===
Total Fields Evaluated: 3553
Total Matches: 3364
Overall Accuracy: 94.7%
```