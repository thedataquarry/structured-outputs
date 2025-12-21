"""
Debug script to compare a single note from the unstructured note.json data.
"""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--index", "-i", type=int, default=1, help="Record index to debug")
args = parser.parse_args()
INDEX_ID = args.index

data_path = Path("../../data")

with open(data_path / "note.json", "r") as f:
    notes = json.load(f)

# pprint(result_data[INDEX_ID - 1])
print(f"Note:\n{notes[INDEX_ID - 1]['note']}")
