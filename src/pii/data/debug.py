"""
Debug script to compare a single record between the source and result FHIR data.
"""
import polars as pl

df = pl.read_parquet("pii.parquet")
print(len(df))

# pprint(result_data[INDEX_ID - 1])
print(df.filter(pl.col("ground_truth").str.contains("Manley")).select(pl.all()).to_dicts())
