import json
import os
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import numpy as np

# Path to your combined JSON file
json_file = "ffi_metrics_sample.json"  # replace with your actual path

with open(json_file, "r") as f:
    data = json.load(f)

total_projects = len(data)

# Stats to track
ffi_counts = {"extern_c": 0, "no_mangle": 0, "link_attrs": 0}
syntax_tree_heights = []
usage_totals = Counter()
ffi_by_usage = defaultdict(lambda: {"ffi": 0, "total": 0})

# Process each project
for project, metrics in data.items():
    # FFI usage
    if metrics["extern_c"] > 0:
        ffi_counts["extern_c"] += 1
    if metrics["no_mangle"] > 0:
        ffi_counts["no_mangle"] += 1
    if metrics["link_attrs"] > 0:
        ffi_counts["link_attrs"] += 1

    # Syntax tree height
    syntax_tree_heights.append(metrics["syntax_tree_height"])

    # Usage classification
    for category in ["kernel", "driver", "library", "sandbox"]:
        usage_totals[category] += metrics["usage"].get(category, 0)
        ffi_sum = metrics["extern_c"] + metrics["no_mangle"] + metrics["link_attrs"]
        if metrics["usage"].get(category, 0) > 0:
            ffi_by_usage[category]["total"] += 1
            if ffi_sum > 0:
                ffi_by_usage[category]["ffi"] += 1

# 1. Percent of projects using FFI
print("\n=== FFI Usage ===")
for k, v in ffi_counts.items():
    print(f"{k}: {v} projects ({v / total_projects * 100:.2f}%)")

# 2. Syntax tree height distribution
print("\n=== Syntax Tree Height ===")
print(f"Min: {min(syntax_tree_heights)}, Max: {max(syntax_tree_heights)}, Avg: {sum(syntax_tree_heights) / total_projects:.2f}")
plt.hist(syntax_tree_heights, bins=range(min(syntax_tree_heights), max(syntax_tree_heights) + 1), edgecolor="black")
plt.title("Syntax Tree Height Distribution")
plt.xlabel("Height")
plt.ylabel("Number of Projects")
plt.grid(True)
plt.show()

# 3. Usage distribution
print("\n=== Usage Distribution ===")
total_usage = sum(usage_totals.values())
for cat in ["kernel", "driver", "library", "sandbox"]:
    pct = (usage_totals[cat] / total_usage) * 100 if total_usage else 0
    print(f"{cat}: {usage_totals[cat]} ({pct:.2f}%)")

# 4. Correlation: FFI by usage
print("\n=== FFI Usage by Category ===")
for cat in ["kernel", "driver", "library", "sandbox"]:
    u = ffi_by_usage[cat]
    if u["total"] > 0:
        rate = u["ffi"] / u["total"]
        print(f"{cat}: {rate:.2%} of projects use FFI ({u['ffi']} / {u['total']})")
    else:
        print(f"{cat}: No projects")

