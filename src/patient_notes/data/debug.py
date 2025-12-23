"""
Debug script to compare a single record between the source and result FHIR data.
"""
import argparse
import json
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument("--index", "-i", type=int, default=1, help="Record index to debug")
args = parser.parse_args()
INDEX_ID = args.index

with open("note.json", "r") as f:
    notes = json.load(f)

# pprint(result_data[INDEX_ID - 1])
print(f"Note:\n{notes[INDEX_ID - 1]['note']}")


