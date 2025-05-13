import os
from collections import defaultdict, Counter
import matplotlib.pyplot as plt

# Directory of .txt files
rust_paths_dir = os.path.join(os.getcwd(), "rs_paths")

# Manual normalization mappings (fuzzy grouping)
normalization_map = {
    "lib": "library",
    "libs": "library",
    "library": "library",
    "driver": "driver",
    "drivers": "driver",
    "drv": "driver",
    "kernel": "kernel",
    "core": "core",
    "hal": "hardware",
    "hw": "hardware"
}

# Explicit categories to track
tracked_categories = set(normalization_map.values())

# For analysis
category_repos = defaultdict(set)
segment_counter = Counter()

# Options
excluded_segments = {
    "src", "main", "tests", "examples", "test", "include",
    "android", "rust", "benches", "doc", "benchmark"
}
included_segments = {"library", "driver", "kernel"}
repo_total = 0

def normalize_segment(segment):
    segment = segment.lower()
    return normalization_map.get(segment, segment)

# Process each repo
for file in os.listdir(rust_paths_dir):
    if file.endswith(".txt"):
        repo_total += 1
        repo_name = file
        with open(os.path.join(rust_paths_dir, file), "r") as f:
            paths = [line.strip() for line in f if line.strip().endswith(".rs")]
        
        seen_segments = set()
        for path in paths:
            segments = set(normalize_segment(p) for p in path.lower().split("/"))
            seen_segments.update(segments)
        
        for seg in seen_segments:
            segment_counter[seg] += 1
            if seg in tracked_categories:
                category_repos[seg].add(repo_name)

# Output to file
with open("rust_paths_classification.txt", "w") as out:
    out.write(f"Total repositories processed: {repo_total}\n\n")
    for cat in tracked_categories:
        out.write(f"Repositories using '{cat}': {len(category_repos[cat])}\n")
    out.write("\nTop 30 normalized directory segments:\n")
    for seg, count in segment_counter.most_common(30):
        out.write(f"{seg}: {count}\n")

# Plotting
def plot_top_segments(n=15, exclude=excluded_segments, include=included_segments):
    filtered = {
    seg: count for seg, count in segment_counter.items()
    if (seg not in exclude or seg in include) and not seg.endswith(".rs")
    }

    top = Counter(filtered).most_common(n)
    labels, values = zip(*top)

    plt.figure(figsize=(10, 6))
    plt.barh(labels[::-1], values[::-1])
    plt.title(f"Top {n} Normalized Rust File Directory Segments")
    plt.xlabel("File Count")
    plt.tight_layout()
    plt.savefig("rust_paths_segments.png")
    plt.show()

def plot_included_segments(included=included_segments):
    included_data = {seg: segment_counter[seg] for seg in included if seg in segment_counter}
    if not included_data:
        return

    labels, values = zip(*included_data.items())

    plt.figure(figsize=(6, 3))
    plt.barh(labels[::-1], values[::-1])
    plt.title("Manually Included Segments")
    plt.xlabel("File Count")
    plt.tight_layout()
    plt.savefig("included_segments.png")
    plt.show()


# Run graph generation
plot_top_segments(n=15)
plot_included_segments()
print(repo_total)
