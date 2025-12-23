# DSPy for structured outputs

This section contains code for getting structured outputs using DSPy with `BAMLAdapter`.

## Usage

```bash
# Extract structured outputs for top 100 business and financial text records
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

The numbers below represent
the percentage of total exact matches from the evaluation script, comparing the structured outputs
against the gold standard. For comparison, the results from DSPy using the BAML adapter
are also shown.

| Model | BAML | DSPy w/ JSON schema | DSPy w/ BAML Adapter |
|-------|---|-------------------:|-------------------:|
| `mistralai/ministral-14b-2512` | 88.7% | 85.8% | 84.8% |
| `google/gemini-2.0-flash-001` | 89.2% | 88.5 | 87.4% |
| `google/gemini-3-flash-preview` | **90.3%** | **90.7%** | **90.8%** |
| `openai/gpt-4.1` | 84.3% | 84.4% | 86.6% |
| `openai/gpt-5.2` | 87.5% | 86.5% | 87.6% |

Smaller, cheaper models tend to do better with BAML, whereas the larger, more capable (and more
recent models) tend to do better with DSPy and `BAMLAdapter`. This is likely because
as the models get better, they are better able to understand the instructions and keep track
of them while handling DSPy's more verbose structured prompts. Smaller models struggle to
keep track of the instructions and BAML's less verbose prompt helps them here.

### Example results

For the first 100 records of the dataset, the results for `google/gemini-3-flash-preview` are shown below.

#### Default, with `JSONAdapter` and JSON schema

```
Matched 100 records for evaluation
=== Field-Level Evaluation Results ===

  Company -> 137/177 (77.4%)
  Date -> 97/111 (87.4%)
  Location -> 111/114 (97.4%)
  Money -> 101/107 (94.4%)
  Person -> 100/101 (99.0%)
  Product -> 72/80 (90.0%)
  Quantity -> 101/103 (98.1%)

=== Overall Statistics ===
Total Fields Evaluated: 793
Total Matches: 719
Overall Accuracy: 90.7%
```