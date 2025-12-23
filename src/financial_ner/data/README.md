# Financial Entities

Extract financial and contextual entities from business and financial text.

Field | Description
--- | ---
Source URL | Business and financial text from [Hugging Face datasets](https://huggingface.co/datasets/Cleanlab/fire-financial-ner-extraction)
Input format | Parquet
Output format | Nested JSON
Number of records | 2,117

The raw data is from the Cleanlab
[structured outputs benchmarks](https://github.com/cleanlab/structured-output-benchmark) repo.

## Evaluation data

To make the data easier to process, the data was preprocessed from its original
parquet form, and the gold dataset was output to a separate JSON file for easy comparison
with the extracted outputs from LLMs.

Download the full data in the source URL listed above and process using your favourite
data processing framework.