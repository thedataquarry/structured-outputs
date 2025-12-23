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

For the first 100 records of the dataset, the results for `google/gemini-3-flash-preview` are shown below.

#### Default, with `JSONAdapter` and JSON schema

```
Matched 100 records for evaluation
=== Field-Level Evaluation Results ===

  ACCOUNTNAME -> 99/100 (99.0%) [mismatches: [38]]
  ACCOUNTNUMBER -> 94/100 (94.0%) [mismatches: [1, 34, 47, 80, 88, 99]]
  AGE -> 97/100 (97.0%) [mismatches: [26, 43, 62]]
  AMOUNT -> 97/100 (97.0%) [mismatches: [60, 77, 91]]
  BIC -> 100/100 (100.0%)
  BITCOINADDRESS -> 100/100 (100.0%)
  BUILDINGNUMBER -> 100/100 (100.0%)
  CITY -> 99/100 (99.0%) [mismatches: [42]]
  COMPANYNAME -> 99/100 (99.0%) [mismatches: [45]]
  COUNTY -> 99/100 (99.0%) [mismatches: [42]]
  CREDITCARDCVV -> 100/100 (100.0%)
  CREDITCARDISSUER -> 100/100 (100.0%)
  CREDITCARDNUMBER -> 97/100 (97.0%) [mismatches: [10, 68, 100]]
  CURRENCY -> 97/100 (97.0%) [mismatches: [1, 29, 45]]
  CURRENCYCODE -> 99/100 (99.0%) [mismatches: [1]]
  CURRENCYNAME -> 98/100 (98.0%) [mismatches: [29, 45]]
  CURRENCYSYMBOL -> 99/100 (99.0%) [mismatches: [45]]
  DATE -> 96/100 (96.0%) [mismatches: [51, 71, 94, 100]]
  DOB -> 94/100 (94.0%) [mismatches: [43, 51, 71, 77, 94, 100]]
  EMAIL -> 100/100 (100.0%)
  ETHEREUMADDRESS -> 100/100 (100.0%)
  EYECOLOR -> 99/100 (99.0%) [mismatches: [13]]
  FIRSTNAME -> 89/100 (89.0%) [mismatches: [14, 20, 41, 47, 48, 65, 71, 78, 83, 91]]
  GENDER -> 95/100 (95.0%) [mismatches: [32, 53, 55, 56, 62]]
  HEIGHT -> 100/100 (100.0%)
  IBAN -> 100/100 (100.0%)
  IP -> 94/100 (94.0%) [mismatches: [16, 17, 24, 31, 69, 83]]
  IPV4 -> 99/100 (99.0%) [mismatches: [69]]
  IPV6 -> 99/100 (99.0%) [mismatches: [83]]
  JOBAREA -> 95/100 (95.0%) [mismatches: [12, 14, 39, 49, 90]]
  JOBTITLE -> 93/100 (93.0%) [mismatches: [7, 21, 25, 35, 40, 43, 47]]
  JOBTYPE -> 96/100 (96.0%) [mismatches: [6, 25, 35, 94]]
  LASTNAME -> 92/100 (92.0%) [mismatches: [15, 20, 47, 48, 79, 83, 86, 98]]
  LITECOINADDRESS -> 100/100 (100.0%)
  MAC -> 100/100 (100.0%)
  MASKEDNUMBER -> 96/100 (96.0%) [mismatches: [8, 10, 88, 100]]
  MIDDLENAME -> 94/100 (94.0%) [mismatches: [14, 15, 41, 71, 79, 91]]
  NEARBYGPSCOORDINATE -> 100/100 (100.0%)
  ORDINALDIRECTION -> 98/100 (98.0%) [mismatches: [69, 97]]
  PASSWORD -> 100/100 (100.0%)
  PHONEIMEI -> 98/100 (98.0%) [mismatches: [1, 3]]
  PHONENUMBER -> 96/100 (96.0%) [mismatches: [3, 34, 43, 83]]
  PIN -> 100/100 (100.0%)
  PREFIX -> 99/100 (99.0%) [mismatches: [28]]
  SECONDARYADDRESS -> 100/100 (100.0%)
  SEX -> 96/100 (96.0%) [mismatches: [32, 53, 55, 62]]
  SSN -> 97/100 (97.0%) [mismatches: [43, 83, 99]]
  STATE -> 99/100 (99.0%) [mismatches: [34]]
  STREET -> 100/100 (100.0%)
  TIME -> 100/100 (100.0%)
  URL -> 100/100 (100.0%)
  USERAGENT -> 100/100 (100.0%)
  USERNAME -> 97/100 (97.0%) [mismatches: [20, 22, 86]]
  VEHICLEVIN -> 100/100 (100.0%)
  VEHICLEVRM -> 100/100 (100.0%)
  ZIPCODE -> 99/100 (99.0%) [mismatches: [73]]

=== Overall Statistics ===
Total Fields Evaluated: 5600
Total Matches: 5484
Overall Accuracy: 97.9%
```