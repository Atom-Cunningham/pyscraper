import pandas as pd

# Load the data
df = pd.read_csv("ffi_metrics_cleaned.csv", index_col=0)

# Separate kernel and driver matches
kernel_df = df[df.index.str.contains("kernel", case=False)].sort_values(by="total_lines", ascending=False)
driver_df = df[df.index.str.contains("driver", case=False) & ~df.index.str.contains("kernel", case=False)].sort_values(by="total_lines", ascending=False)

# Combine them (kernel first)
combined = pd.concat([kernel_df, driver_df])

# Save to output file
combined.to_csv("find_kernel_driver.csv")

# Print repo names
print("Repositories matching 'kernel' or 'driver':")
for name in combined.index:
    print(name)
