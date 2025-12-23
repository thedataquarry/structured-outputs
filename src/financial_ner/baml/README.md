# BAML for structured outputs

This section contains code for getting structured outputs using BAML.

## Usage

```bash
# Extract structured outputs for top 100 business and financial text records
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
| `mistralai/ministral-14b-2512` | 88.7% | 85.8% | 84.8% |
| `google/gemini-2.0-flash-001` | 89.2% | 88.5 | 87.4% |
| `google/gemini-3-flash-preview` | 90.3% | 90.7% | **90.8%** |
| `openai/gpt-4.1` | 84.3% | 84.4% | 86.6% |
| `openai/gpt-5.2` | 87.5% | 86.5% | 87.6% |

Smaller, cheaper models tend to do better with BAML, whereas the larger, more capable (and more
recent models) tend to do better with DSPy and `BAMLAdapter`. This is likely because
as the models get better, they are better able to understand the instructions and keep track
of them while handling DSPy's more verbose structured prompts. Smaller models struggle to
keep track of the instructions and BAML's less verbose prompt helps them here.

### Example results

For the 100 records of the dataset, the results for `google/gemini-3-flash-preview` are shown below.

```
Matched 100 records for evaluation
=== Field-Level Evaluation Results ===

  Company -> 135/177 (76.3%)
  Date -> 99/111 (89.2%)
  Location -> 109/114 (95.6%)
  Money -> 100/107 (93.5%)
  Person -> 100/101 (99.0%)
  Product -> 69/76 (90.8%)
  Quantity -> 97/99 (98.0%)

=== Overall Statistics ===
Total Fields Evaluated: 785
Total Matches: 709
Overall Accuracy: 90.3%
```
