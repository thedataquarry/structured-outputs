import ast
import polars as pl

df = pl.read_csv('hf://datasets/Cleanlab/fire-financial-ner-extraction/fire_financial_ner_extraction.csv')

# Write out dataset as parquet file
df.write_parquet("financial_ner.parquet")

# Write out gold data as JSON for ease of evaluation
ground_truth = (
    df.select(
        pl.col("ground_truth").map_elements(
            ast.literal_eval,
            return_dtype=pl.Object,
        )
    )
    .get_column("ground_truth")
    .to_list()
)

# Write to JSON
with open("gold.json", "w") as f:
    import json

    json.dump(ground_truth, f)
