import pandas as pd
import json
from pathlib import Path

# ===== Paths =====
data_dir = Path("../ground_truth_dataset")

# ===== Load CSVs =====
df_packageversions = pd.read_csv(data_dir / "Package_info.csv", low_memory=False)
df_pvp = pd.read_csv(data_dir / "Project_Packageversions.csv", low_memory=False)
df_projects = pd.read_csv(data_dir / "Project_info.csv", low_memory=False)

# ===== Step 1: Filter Package_info =====
# Keep only NPM systems
df_pkg_filtered = df_packageversions[df_packageversions["System"] == "NPM"].copy()

# Ensure VersionInfo is parsed as JSON to extract isRelease
def is_release_true(version_info):
    try:
        vi = json.loads(version_info) if isinstance(version_info, str) else version_info
        return bool(vi.get("IsRelease", False))
    except Exception:
        return False

df_pkg_filtered["IsRelease"] = df_pkg_filtered["VersionInfo"].apply(is_release_true)
df_pkg_filtered = df_pkg_filtered[df_pkg_filtered["IsRelease"] == True]

# ===== Step 2: Join with Project_Packageversions =====
# Match on Name + Version
df_join1 = pd.merge(
    df_pvp,
    df_pkg_filtered[["Name", "Version"]],
    on=["Name", "Version"],
    how="inner"
)

# ===== Step 3: Join with Project_info =====
# We'll need to check MIT license in Licenses column (JSON array or string)
def has_mit_license(licenses_str):
    if not isinstance(licenses_str, str):
        return False
    try:
        lic_list = json.loads(licenses_str)
        if isinstance(lic_list, list):
            return any("MIT" in lic for lic in lic_list)
        elif isinstance(lic_list, str):
            return "MIT" in lic_list
    except Exception:
        # Handle cases where the string is not valid JSON
        return "MIT" in licenses_str
    return False

df_projects["HasMIT"] = df_projects["Licenses"].apply(has_mit_license)

# Filter to MIT projects
df_projects_mit = df_projects[df_projects["HasMIT"] == True]

# Join PVP->Projects on ProjectType+ProjectName to Type+Name
df_join2 = pd.merge(
    df_join1,
    df_projects_mit,
    left_on=["ProjectType", "ProjectName"],
    right_on=["Type", "Name"],
    how="inner"
)

# ===== Step 4: Sort by ForksCount and keep top 5 unique projects =====
# Drop duplicate project names, keeping the one with highest ForksCount
df_join2_sorted = df_join2.sort_values(by="ForksCount", ascending=False)
df_top5 = df_join2_sorted.drop_duplicates(subset=["ProjectName"]).head(5)

# ===== Step 5: Keep only desired output columns =====
df_result = df_top5[["ProjectName", "Version", "ForksCount"]].reset_index(drop=True)

# ===== Save result =====
output_path = "ground_truth.csv"
df_result.to_csv(output_path, index=False, encoding="utf-8-sig")

print("✅ Query complete. Results saved to:", output_path)
print(df_result)
