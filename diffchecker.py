import json
import sys

if len(sys.argv) != 3:
    print("Usage: python find_missing_entries.py <base.json> <to_check.json>")
    sys.exit(1)

with open(sys.argv[1]) as f1, open(sys.argv[2]) as f2:
    base = json.load(f1)
    to_check = json.load(f2)

missing = [name for name in base if name not in to_check]

print("Missing entries:")
for name in missing:
    print(name)
