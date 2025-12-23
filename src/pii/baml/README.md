# BAML for structured outputs

This section contains code for getting structured outputs using BAML.

## Usage

```bash
# Extract structured outputs for all 100 PII extraction records
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
| `mistralai/ministral-14b-2512` | 95.8% | 96.3% | ❌ |
| `google/gemini-2.0-flash-001` | 96.4% | 96.6% | 96.3% |
| `google/gemini-3-flash-preview` | 96.7% | **97.9%** | 96.9% |
| `openai/gpt-4.1` | **97.1%** | 97.4% | **97.4%** |
| `openai/gpt-5.2` | 96.7% | 97.5% | 97.3% |

In these results, interestingly, DSPy-default (based on the `ChatAdapter`) does the best among all
three approaches. Because the JSON structure being modeled is rather flat, long, and sparse, it
seems like the combination of the structured prompting strategy of DSPy + clearly defined JSON
schema give all models the context they need. In BAML's and the `BAMLAdapter` + DSPy case, the
benefits aren't as apparent because the models are able to handle the flat (single-level nested)
JSON easily enough using JSON schema.

### Example results

For the 100 records of the dataset, the results for `google/gemini-3-flash-preview` are shown below.

```
Matched 100 records for evaluation
=== Field-Level Evaluation Results ===

  ACCOUNTNAME -> 99/100 (99.0%) [mismatches: [38]]
  ACCOUNTNUMBER -> 94/100 (94.0%) [mismatches: [1, 29, 34, 80, 88, 99]]
  AGE -> 94/100 (94.0%) [mismatches: [26, 27, 43, 55, 58, 62]]
  AMOUNT -> 95/100 (95.0%) [mismatches: [8, 41, 60, 77, 91]]
  BIC -> 100/100 (100.0%)
  BITCOINADDRESS -> 100/100 (100.0%)
  BUILDINGNUMBER -> 99/100 (99.0%) [mismatches: [77]]
  CITY -> 98/100 (98.0%) [mismatches: [42, 82]]
  COMPANYNAME -> 96/100 (96.0%) [mismatches: [7, 45, 88, 96]]
  COUNTY -> 98/100 (98.0%) [mismatches: [42, 58]]
  CREDITCARDCVV -> 100/100 (100.0%)
  CREDITCARDISSUER -> 100/100 (100.0%)
  CREDITCARDNUMBER -> 97/100 (97.0%) [mismatches: [10, 68, 100]]
  CURRENCY -> 92/100 (92.0%) [mismatches: [4, 9, 28, 41, 60, 70, 74, 91]]
  CURRENCYCODE -> 95/100 (95.0%) [mismatches: [1, 9, 41, 60, 74]]
  CURRENCYNAME -> 88/100 (88.0%) [mismatches: [1, 9, 21, 28, 29, 41, 45, 60, 70, 74]]
  CURRENCYSYMBOL -> 99/100 (99.0%) [mismatches: [77]]
  DATE -> 94/100 (94.0%) [mismatches: [26, 51, 58, 71, 94, 100]]
  DOB -> 94/100 (94.0%) [mismatches: [43, 51, 71, 77, 94, 100]]
  EMAIL -> 100/100 (100.0%)
  ETHEREUMADDRESS -> 100/100 (100.0%)
  EYECOLOR -> 99/100 (99.0%) [mismatches: [13]]
  FIRSTNAME -> 88/100 (88.0%) [mismatches: [20, 41, 47, 58, 65, 71, 72, 78, 81, 91]]
  GENDER -> 96/100 (96.0%) [mismatches: [53, 55, 56, 61]]
  HEIGHT -> 100/100 (100.0%)
  IBAN -> 100/100 (100.0%)
  IP -> 88/100 (88.0%) [mismatches: [6, 16, 17, 18, 24, 27, 28, 31, 52, 62]]
  IPV4 -> 98/100 (98.0%) [mismatches: [33, 69]]
  IPV6 -> 98/100 (98.0%) [mismatches: [33, 83]]
  JOBAREA -> 83/100 (83.0%) [mismatches: [6, 12, 14, 18, 21, 24, 39, 49, 52, 64]]
  JOBTITLE -> 89/100 (89.0%) [mismatches: [6, 7, 15, 24, 25, 35, 40, 43, 47, 96]]
  JOBTYPE -> 96/100 (96.0%) [mismatches: [6, 25, 35, 72]]
  LASTNAME -> 92/100 (92.0%) [mismatches: [14, 15, 20, 65, 72, 79, 81, 98]]
  LITECOINADDRESS -> 100/100 (100.0%)
  MAC -> 100/100 (100.0%)
  MASKEDNUMBER -> 96/100 (96.0%) [mismatches: [8, 10, 88, 100]]
  MIDDLENAME -> 92/100 (92.0%) [mismatches: [14, 15, 41, 47, 71, 79, 91, 95]]
  NEARBYGPSCOORDINATE -> 100/100 (100.0%)
  ORDINALDIRECTION -> 99/100 (99.0%) [mismatches: [97]]
  PASSWORD -> 100/100 (100.0%)
  PHONEIMEI -> 98/100 (98.0%) [mismatches: [1, 3]]
  PHONENUMBER -> 94/100 (94.0%) [mismatches: [3, 34, 43, 58, 83, 99]]
  PIN -> 100/100 (100.0%)
  PREFIX -> 99/100 (99.0%) [mismatches: [28]]
  SECONDARYADDRESS -> 100/100 (100.0%)
  SEX -> 93/100 (93.0%) [mismatches: [25, 26, 32, 43, 56, 61, 62]]
  SSN -> 97/100 (97.0%) [mismatches: [43, 83, 99]]
  STATE -> 99/100 (99.0%) [mismatches: [82]]
  STREET -> 98/100 (98.0%) [mismatches: [77, 88]]
  TIME -> 100/100 (100.0%)
  URL -> 100/100 (100.0%)
  USERAGENT -> 100/100 (100.0%)
  USERNAME -> 94/100 (94.0%) [mismatches: [22, 48, 56, 65, 74, 81]]
  VEHICLEVIN -> 100/100 (100.0%)
  VEHICLEVRM -> 100/100 (100.0%)
  ZIPCODE -> 99/100 (99.0%) [mismatches: [73]]

=== Overall Statistics ===
Total Fields Evaluated: 5600
Total Matches: 5417
Overall Accuracy: 96.7%
```
