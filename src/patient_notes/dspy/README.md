# DSPy for structured outputs

This section contains code for getting structured outputs using DSPy with `BAMLAdapter`.

## Usage

```bash
# Extract structured outputs for the first 100 patient notes
uv run extract.py -e 100
# Extract from all 2,726 patient notes
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
| `mistralai/ministral-14b-2512` | 95.7% | ❌ | ❌ |
| `google/gemini-2.0-flash-001` | 96.3% | 87.6% | 96.6%x |
| `google/gemini-3-flash-preview` | 96.3% | 93.1% | 95.1% |
| `openai/gpt-4.1` | **97.4%** | **95.6%** | **96.8%** |
| `openai/gpt-5-mini` | 96.1% | ❌ | 95.8% |
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

#### With `BAMLAdapter`
```
Matched 100 records for evaluation
=== Field-Level Evaluation Results ===

Patient Fields:
  patient.address.city -> 63/63 (100.0%)
  patient.address.country -> 63/63 (100.0%)
  patient.address.line -> 57/63 (90.5%) [mismatches: [39, 41, 75, 85, 90, 97]]
  patient.address.postalCode -> 57/63 (90.5%) [mismatches: [8, 28, 33, 34, 39, 100]]
  patient.address.state -> 63/63 (100.0%)
  patient.age -> 100/100 (100.0%)
  patient.birthDate -> 100/100 (100.0%)
  patient.email -> 100/100 (100.0%)
  patient.gender -> 92/100 (92.0%) [mismatches: [20, 44, 49, 56, 58, 72, 79, 89]]
  patient.maritalStatus -> 98/100 (98.0%) [mismatches: [64, 100]]
  patient.name.family -> 98/100 (98.0%) [mismatches: [45, 97]]
  patient.name.given -> 100/100 (100.0%)
  patient.name.prefix -> 95/100 (95.0%) [mismatches: [13, 15, 28, 37, 80]]
  patient.phone -> 100/100 (100.0%)

Practitioner Fields:
  practitioner.address.city -> 16/16 (100.0%)
  practitioner.address.country -> 16/16 (100.0%)
  practitioner.address.line -> 25/38 (65.8%) [mismatches: [14, 20, 25, 28, 29, 33, 44, 45, 47, 63]]
  practitioner.address.postalCode -> 12/16 (75.0%) [mismatches: [20, 27, 34, 63]]
  practitioner.address.state -> 16/16 (100.0%)
  practitioner.email -> 38/38 (100.0%)
  practitioner.name.family -> 37/38 (97.4%) [mismatches: [27]]
  practitioner.name.given -> 37/38 (97.4%) [mismatches: [27]]
  practitioner.name.prefix -> 38/38 (100.0%)
  practitioner.phone -> 37/38 (97.4%) [mismatches: [52]]

Practitioner Count Fields:
  practitioner.count -> 96/100 (96.0%) [mismatches: [66, 73, 82, 93]]

Immunization Fields:
  immunization.count -> 94/100 (94.0%) [mismatches: [11, 14, 17, 53, 71, 77]]

Allergy Fields:
  allergy.count -> 100/100 (100.0%)

=== Overall Statistics ===
Total Fields Evaluated: 1807
Total Matches: 1748
Overall Accuracy: 96.7%
```