import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Load JSON
with open('ffi_metrics.json', 'r') as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame.from_dict(data, orient='index')
usage_df = df['usage'].apply(pd.Series)
df = df.drop(columns=['usage']).join(usage_df)

# Summary table
summary_stats = df.describe().loc[['mean', '50%', 'max']].rename(index={'50%': 'median'})
summary_stats.to_csv("ffi_summary_stats.csv")

# --- Usage Role Bar Chart (excluding "other") ---
usage_totals = usage_df.drop(columns='other', errors='ignore').sum().sort_values()
usage_totals.plot(kind='barh', title='Total .rs files by Usage Role (Excludes "Other")')
plt.tight_layout()
plt.savefig("usage_roles_bar_chart.png")
plt.close()

# Print count of 'other' for caption
other_count = usage_df['other'].sum() if 'other' in usage_df.columns else 0
print(f"[INFO] 'Other' category count: {other_count} files not explicitly categorized.")

# --- FFI Density Histogram (truncated) ---
df[df['ffi_density_per_kloc'] <= 90]['ffi_density_per_kloc'].plot(
    kind='hist', bins=30, title='Histogram of FFI Density per 1KLOC (x ≤ 90)'
)
plt.xlabel('FFI Density per 1KLOC')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig("ffi_density_histogram_truncated.png")
plt.close()

# --- Unsafe Count (Raw and Normalized) ---
top_unsafe_raw = df['unsafe_count'].sort_values(ascending=False).head(10)
top_unsafe_norm = (df['unsafe_count'] / df['total_lines'] * 1000).sort_values(ascending=False).head(10)

# Clean labels for plotting
def clean_label(label):
    parts = label.split('/')
    to_strip = {'platform', 'external', 'rust'}
    while parts and parts[0] in to_strip:
        parts.pop(0)
    return '/'.join(parts)

clean_index = df.index.map(clean_label)
rename_map = dict(zip(df.index, clean_index))

# Plot raw unsafe count
top_unsafe_raw.rename(index=rename_map).plot(kind='bar', title='Top 10 Repos by Unsafe Block Count')
plt.ylabel('Unsafe Block Count')
plt.tight_layout()
plt.savefig("top10_unsafe_repos_raw.png")
plt.close()

# Plot normalized unsafe count
top_unsafe_norm.rename(index=rename_map).plot(kind='bar', title='Top 10 Repos by Unsafe Blocks per KLOC')
plt.ylabel('Unsafe Blocks per KLOC')
plt.tight_layout()
plt.savefig("top10_unsafe_repos_per_kloc.png")
plt.close()


# --- PCA (2D) on selected numeric features ---

# Exclude non-numeric or derived/categorical traits
ignored_traits = ['kernel', 'driver', 'sandbox', 'library', 'other','syntax_tree_height', 'average_file_depth']

features = [col for col in df.columns if col not in ignored_traits]
pca_data = df[features].fillna(0)
pca_scaled = StandardScaler().fit_transform(pca_data)

pca = PCA(n_components=2)
principal_components = pca.fit_transform(pca_scaled)

pca_df = pd.DataFrame(data=principal_components, columns=['PC1', 'PC2'], index=df.index)

#handle outliers
# Compute Euclidean distances from the origin in PCA space
pca_df['distance'] = np.sqrt(pca_df['PC1']**2 + pca_df['PC2']**2)

# Find the repo with the maximum distance
outlier_repo = pca_df['distance'].idxmax()
outlier_distance = pca_df.loc[outlier_repo, 'distance']
print(f"[INFO] PCA outlier detected: {outlier_repo} (distance = {outlier_distance:.2f})")

plt.figure(figsize=(8, 6))
plt.scatter(pca_df['PC1'], pca_df['PC2'], alpha=0.6)
plt.title('PCA of Rust FFI Metrics (2D)')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.grid(True)
plt.tight_layout()
plt.savefig("ffi_pca_2d.png")
plt.close()

# Optional: save PCA coordinates
pca_df.to_csv("ffi_pca_coords.csv")

#---------PCA2, cleaned and normalized

# Create normalized, scale-independent features
df['unsafe_blocks_per_kloc'] = df['unsafe_count'] / df['total_lines'] * 1000
df['unsafe_fn_per_kloc'] = df['unsafe_fn_count'] / df['total_lines'] * 1000
df['no_mangle_per_kloc'] = df['no_mangle'] / df['total_lines'] * 1000
df['extern_c_per_kloc'] = df['extern_c'] / df['total_lines'] * 1000


pca_features = [
    'unsafe_blocks_per_kloc',
    'unsafe_fn_per_kloc',
    'no_mangle_per_kloc',
    'extern_c_per_kloc',
    'ffi_density_per_kloc'
]
pca_data = df[pca_features].replace([np.inf, -np.inf], np.nan).fillna(0)

# Remove the outlier from both PCA input and original DataFrame
pca_data_cleaned = pca_data.drop(index=outlier_repo)
df_cleaned = df.drop(index=outlier_repo)

# Rerun PCA
pca_scaled_cleaned = StandardScaler().fit_transform(pca_data_cleaned)
pca_cleaned = PCA(n_components=2)
principal_components_cleaned = pca_cleaned.fit_transform(pca_scaled_cleaned)

# Plot new PCA
pca_df_cleaned = pd.DataFrame(
    data=principal_components_cleaned,
    columns=['PC1', 'PC2'],
    index=pca_data_cleaned.index
)

plt.figure(figsize=(8, 6))
plt.scatter(pca_df_cleaned['PC1'], pca_df_cleaned['PC2'], alpha=0.6)
plt.title('PCA of Rust FFI Metrics (Outlier Removed)')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.grid(True)
plt.tight_layout()
plt.savefig("ffi_pca_2d_no_outlier.png")
plt.close()

# Save cleaned PCA and outlier info
pca_df_cleaned.to_csv("ffi_pca_coords_no_outlier.csv")

for i, comp in enumerate(pca.components_):
    print(f"PC{i+1} loadings:")
    for feature, weight in zip(pca_data.columns, comp):
        print(f"  {feature}: {weight:.3f}")

print(pca.explained_variance_ratio_)

print("[DONE] Figures and tables saved.")

