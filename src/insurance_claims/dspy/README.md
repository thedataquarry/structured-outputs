# DSPy for structured outputs

This section contains code for getting structured outputs using DSPy with `BAMLAdapter`.

## Usage

```bash
# Extract structured outputs for all 30 records
uv run extract.py
```

The results are saved to `data/structured_output_dspy.json`.

## JSON schema vs. BAML adapter

By default, DSPy uses a JSON schema to transform the types from the signatures to render the
prompt for the LM. This is the default behavior in the `extract.py` script. However, we can
significantly improve the structured output results by using a [custom DSPy adapter](https://dspy.ai/learn/programming/language_models/?h=adapter#advanced-building-custom-lms-and-writing-your-own-adapters)
that applies the BAML format.

This adapter generates a compact, human-readable schema representation for nested Pydantic output
fields, inspired by the JSON formatter used by [BAML](https://github.com/BoundaryML/baml),
an open source programming language to interact with LLMs and produce high-quality structured outputs.
The schema rendered by this adapter is more token-efficient and easier for all LMs to follow than
a raw JSON schema. It includes Pydantic field descriptions as comments in the schema, which
provide valuable additional context for the LM to understand the expected output.

Experimental results below show that the BAML adapter is universally better than providing JSON
schema to the LLM via the signature.

## Evaluation

An evaluation script is provided to compare the extracted structured outputs against a gold standard.
The gold standard file is `data/gold.json`, and is obtained by processing the raw JSON data in FHIR
format and reformatting it to match the expected output structure from the DSPy script.

```bash
uv run evaluate.py
```

## Results

Experiments were run for several LMs, with and without the BAML adapter. The numbers below represent
the percentage of total exact matches from the evaluation script, comparing the structured outputs
against the gold standard. It's clear that the BAML adapter significantly improves the results across all models.

| Model | BAML | DSPy w/ JSON schema | DSPy w/ BAML Adapter |
|-------|---|-------------------:|-------------------:|
| `mistralai/ministral-14b-2512` | 86.7% | 82.9% | 87.0% |
| `google/gemini-2.0-flash-001` | 85.7% | 85.5% | 86.8% |
| `google/gemini-3-flash-preview` | **86.1%** | 83.8% | 87.7% |
| `openai/gpt-4.1` | 84.3% | 86.9% | 89.8% |
| `openai/gpt-5-mini` | 86.0% | 85.8% | 88.5% |
| `openai/gpt-5.2` | **86.1%** | 85.8% | **91.8%** |

BAML performs better than DSPy-default, which uses `JSONAdapter` or `ChatAdapter`. However, when we pass
use the `BAMLAdapter` in DSPy to pass in the BAML schema format to DSPy's generated prompt,
we see DSPy's performance on par with (or better than) BAML's on most counts.

The performance gains from using the BAML adapter in DSPy come for *free* - all it does is translate
the nested Pydantic types from the signature to a more token-efficient and concise schema representation,
which is then passed to the auto-generated prompt to the LM. This allows the LM to focus on the schema at
hand and adhere to it during generation.

### Example results

For the first 200 records of the dataset, the results for `google/gemini-2.0-flash-001` are shown below.

#### Default, with `JSONAdapter` and JSON schema

```
Patient Fields:
  patient.address.city -> 119/125 (95.2%) [mismatches: [24, 129, 138, 168, 172, 197]]
  patient.address.country -> 115/125 (92.0%) [mismatches: [24, 51, 97, 102, 125, 129, 138, 168, 172, 197]]
  patient.address.line -> 110/125 (88.0%) [mismatches: [24, 39, 41, 75, 85, 90, 97, 103, 115, 129]]
  patient.address.postalCode -> 109/125 (87.2%) [mismatches: [8, 24, 28, 33, 34, 39, 100, 116, 129, 138]]
  patient.address.state -> 119/125 (95.2%) [mismatches: [24, 129, 138, 168, 172, 197]]
  patient.age -> 132/199 (66.3%) [mismatches: [2, 5, 8, 17, 20, 21, 23, 24, 26, 27]]
  patient.birthDate -> 197/199 (99.0%) [mismatches: [51, 179]]
  patient.email -> 198/199 (99.5%) [mismatches: [138]]
  patient.gender -> 153/199 (76.9%) [mismatches: [2, 10, 12, 17, 20, 23, 34, 39, 41, 44]]
  patient.maritalStatus -> 179/199 (89.9%) [mismatches: [10, 17, 23, 49, 57, 58, 64, 100, 103, 111]]
  patient.name.family -> 196/199 (98.5%) [mismatches: [45, 97, 180]]
  patient.name.given -> 195/199 (98.0%) [mismatches: [35, 129, 137, 180]]
  patient.name.prefix -> 165/199 (82.9%) [mismatches: [12, 13, 15, 17, 23, 28, 34, 37, 38, 39]]
  patient.phone -> 199/199 (100.0%)

Practitioner Fields:
  practitioner.address.city -> 35/37 (94.6%) [mismatches: [15, 166]]
  practitioner.address.country -> 34/37 (91.9%) [mismatches: [15, 141, 166]]
  practitioner.address.line -> 49/73 (67.1%) [mismatches: [14, 15, 20, 25, 27, 28, 29, 33, 44, 45]]
  practitioner.address.postalCode -> 31/37 (83.8%) [mismatches: [15, 34, 117, 138, 166, 171]]
  practitioner.address.state -> 35/37 (94.6%) [mismatches: [15, 166]]
  practitioner.email -> 70/73 (95.9%) [mismatches: [117, 138, 166]]
  practitioner.name.family -> 70/73 (95.9%) [mismatches: [27, 138, 166]]
  practitioner.name.given -> 17/73 (23.3%) [mismatches: [8, 9, 10, 13, 14, 17, 24, 25, 27, 28]]
  practitioner.name.prefix -> 71/73 (97.3%) [mismatches: [138, 166]]
  practitioner.phone -> 61/73 (83.6%) [mismatches: [20, 27, 34, 52, 117, 121, 127, 139, 150, 166]]

Practitioner Count Fields:
  practitioner.count -> 194/199 (97.5%) [mismatches: [23, 73, 140, 165, 196]]

Immunization Fields:
  immunization.count -> 195/199 (98.0%) [mismatches: [14, 77, 138, 162]]

Allergy Fields:
  allergy.count -> 194/199 (97.5%) [mismatches: [45, 114, 151, 166, 195]]

=== Overall Statistics ===
Total Fields Evaluated: 3599
Total Matches: 3242
Overall Accuracy: 90.1%
```

#### With `BAMLAdapter`
```
Matched 199 records for evaluation
=== Field-Level Evaluation Results ===

Patient Fields:
  patient.address.city -> 118/124 (95.2%) [mismatches: [24, 129, 150, 168, 172, 197]]
  patient.address.country -> 116/124 (93.5%) [mismatches: [24, 51, 102, 129, 150, 168, 172, 197]]
  patient.address.line -> 108/124 (87.1%) [mismatches: [24, 39, 41, 75, 85, 90, 97, 103, 115, 129]]
  patient.address.postalCode -> 108/124 (87.1%) [mismatches: [8, 24, 28, 33, 34, 39, 100, 116, 129, 141]]
  patient.address.state -> 118/124 (95.2%) [mismatches: [24, 129, 150, 168, 172, 197]]
  patient.age -> 193/199 (97.0%) [mismatches: [59, 66, 81, 112, 128, 182]]
  patient.birthDate -> 197/199 (99.0%) [mismatches: [169, 179]]
  patient.email -> 199/199 (100.0%)
  patient.gender -> 172/199 (86.4%) [mismatches: [2, 17, 20, 33, 44, 45, 46, 49, 56, 58]]
  patient.maritalStatus -> 194/199 (97.5%) [mismatches: [64, 100, 103, 174, 182]]
  patient.name.family -> 196/199 (98.5%) [mismatches: [45, 97, 180]]
  patient.name.given -> 197/199 (99.0%) [mismatches: [129, 180]]
  patient.name.prefix -> 193/199 (97.0%) [mismatches: [13, 15, 37, 80, 106, 141]]
  patient.phone -> 198/199 (99.5%) [mismatches: [150]]

Practitioner Fields:
  practitioner.address.city -> 35/37 (94.6%) [mismatches: [166, 187]]
  practitioner.address.country -> 35/37 (94.6%) [mismatches: [166, 187]]
  practitioner.address.line -> 51/72 (70.8%) [mismatches: [14, 20, 25, 28, 29, 33, 44, 45, 47, 63]]
  practitioner.address.postalCode -> 32/37 (86.5%) [mismatches: [34, 117, 138, 139, 166]]
  practitioner.address.state -> 36/37 (97.3%) [mismatches: [166]]
  practitioner.email -> 71/72 (98.6%) [mismatches: [138]]
  practitioner.name.family -> 70/72 (97.2%) [mismatches: [138, 166]]
  practitioner.name.given -> 70/72 (97.2%) [mismatches: [138, 166]]
  practitioner.name.prefix -> 70/72 (97.2%) [mismatches: [138, 166]]
  practitioner.phone -> 69/72 (95.8%) [mismatches: [52, 150, 166]]

Practitioner Count Fields:
  practitioner.count -> 189/199 (95.0%) [mismatches: [23, 66, 68, 73, 140, 158, 165, 172, 196, 197]]

Immunization Fields:
  immunization.count -> 195/199 (98.0%) [mismatches: [14, 77, 138, 162]]

Allergy Fields:
  allergy.count -> 197/199 (99.0%) [mismatches: [45, 195]]

=== Overall Statistics ===
Total Fields Evaluated: 3588
Total Matches: 3427
Overall Accuracy: 95.5%
```