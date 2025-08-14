import pandas as pd
from pathlib import Path
import json

# ========== Configuration ==========
# Set the directory where the CSV files are located
data_dir = Path("../ground_truth_dataset")
output_path = Path("ground_truth.csv")

# ========== Load CSV files ==========
# Package_info.csv: contains package metadata (including VersionInfo JSON)
# Project_Packageversions.csv: mapping between packages and projects
# Project_info.csv: project metadata (including StarsCount, ForksCount, etc.)
df_packageversions = pd.read_csv(data_dir / "Package_info.csv", low_memory=False)
df_pvp = pd.read_csv(data_dir / "Project_Packageversions.csv", low_memory=False)
df_projects = pd.read_csv(data_dir / "Project_info.csv", low_memory=False)

# ========== Step 1: HighestReleases ==========
# Filter only NPM packages where VersionInfo.IsRelease = True
df_pkg_filtered = df_packageversions[
    (df_packageversions["System"] == "NPM") &
    (df_packageversions["VersionInfo"].apply(
        lambda x: json.loads(x).get("IsRelease") if pd.notnull(x) else False
    ) == True)
].copy()

# Extract Ordinal from VersionInfo JSON
df_pkg_filtered["Ordinal"] = df_pkg_filtered["VersionInfo"].apply(
    lambda x: json.loads(x).get("Ordinal") if pd.notnull(x) else None
)

# For each Name, keep the row with the highest Ordinal
df_highest_releases = (
    df_pkg_filtered.sort_values(["Name", "Ordinal"], ascending=[True, False])
    .groupby("Name", as_index=False)
    .first()[["Name", "Version"]]
)

# ========== Step 2: Filter Project_Packageversions ==========
# Join with HighestReleases
df_pvp_filtered = df_pvp.merge(
    df_highest_releases,
    on=["Name", "Version"],
    how="inner"
)

# Keep only NPM system and GitHub project type
df_pvp_filtered = df_pvp_filtered[
    (df_pvp_filtered["System"] == "NPM") &
    (df_pvp_filtered["ProjectType"] == "GITHUB")
]

# ========== Step 3: Join with Project_info ==========
df_result = df_pvp_filtered.merge(
    df_projects,
    left_on=["ProjectType", "ProjectName"],
    right_on=["Type", "Name"],
    how="inner"
)

# ========== Step 4: Sort by StarsCount and keep top 8 unique Names ==========
df_result_sorted = df_result.sort_values("StarsCount", ascending=False)

# Keep only the first occurrence of each Name_x (highest StarsCount)
df_unique_names = df_result_sorted.drop_duplicates(subset=["Name_x"], keep="first")

# Take the top 5
df_result_top5 = df_unique_names.head(5)

# Keep only Name and Version columns
df_final = df_result_top5[["Name_x", "Version"]].rename(columns={"Name_x": "Name"})

# Save the result
df_final.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"✅ Final unique-name result saved to: {output_path}")
print(df_final)