# BAML for structured outputs

This section contains code for getting structured outputs using BAML.

## Usage

```bash
# Extract structured outputs for all 30 insurance claims records
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
| `mistralai/ministral-14b-2512` | 86.7% | 82.9% | 87.0% |
| `google/gemini-2.0-flash-001` | 85.7% | 85.5% | 86.8% |
| `google/gemini-3-flash-preview` | 86.1% | 83.8% | 87.7% |
| `openai/gpt-4.1` | 84.3% | 86.9% | 89.8% |
| `openai/gpt-5.2` | 86.1% | 85.8% | **91.8%** |

BAML performs better than DSPy-default, which uses `JSONAdapter` or `ChatAdapter`. However, when we pass
use the `BAMLAdapter` in DSPy to pass in the BAML schema format to DSPy's generated prompt,
we see DSPy's performance on par with (or better than) BAML's on most counts.

### Example results

For the 30 records of the dataset, the results for `google/gemini-3-flash-preview` are shown below.

```
Matched 30 records for evaluation
=== Field-Level Evaluation Results ===

  header.channel -> 29/30 (96.7%) [mismatches: [29]]
  header.claim_id -> 29/30 (96.7%) [mismatches: [26]]
  header.incident_date -> 30/30 (100.0%)
  header.report_date -> 30/30 (100.0%)
  header.reported_by -> 30/30 (100.0%)
  incident_description.estimated_damage_amount -> 29/30 (96.7%) [mismatches: [15]]
  incident_description.incident_type -> 26/30 (86.7%) [mismatches: [8, 9, 12, 27]]
  incident_description.location_type -> 29/30 (96.7%) [mismatches: [1]]
  incident_description.police_report_number -> 30/30 (100.0%)
  insured_objects[0].estimated_value -> 23/30 (76.7%) [mismatches: [3, 8, 9, 11, 12, 15, 26]]
  insured_objects[0].location_address -> 22/30 (73.3%) [mismatches: [3, 9, 10, 11, 12, 18, 26, 28]]
  insured_objects[0].make_model -> 22/30 (73.3%) [mismatches: [3, 5, 9, 11, 12, 17, 26, 28]]
  insured_objects[0].object_id -> 13/30 (43.3%) [mismatches: [3, 5, 6, 8, 9, 11, 12, 13, 14, 18]]
  insured_objects[0].object_type -> 25/30 (83.3%) [mismatches: [3, 9, 11, 12, 26]]
  insured_objects[0].year -> 25/30 (83.3%) [mismatches: [3, 9, 11, 12, 26]]
  insured_objects[1].estimated_value -> 2/2 (100.0%)
  insured_objects[1].location_address -> 1/2 (50.0%) [mismatches: [4]]
  insured_objects[1].make_model -> 2/2 (100.0%)
  insured_objects[1].object_id -> 2/2 (100.0%)
  insured_objects[1].object_type -> 2/2 (100.0%)
  insured_objects[1].year -> 2/2 (100.0%)
  policy_details.coverage_type -> 25/26 (96.2%) [mismatches: [26]]
  policy_details.effective_date -> 25/26 (96.2%) [mismatches: [26]]
  policy_details.expiration_date -> 24/26 (92.3%) [mismatches: [24, 26]]
  policy_details.policy_number -> 25/26 (96.2%) [mismatches: [26]]
  policy_details.policyholder_name -> 25/26 (96.2%) [mismatches: [26]]

=== Overall Statistics ===
Total Fields Evaluated: 592
Total Matches: 527
Overall Accuracy: 89.0%
```