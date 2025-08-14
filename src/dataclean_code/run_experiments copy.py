import re
import os
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common_scaffold.agent_tools import run_baseline_agent

def find_query_dirs(project_dir: Path):
    """
    Find all queryN folders (where N is a number) in the project dir.
    """
    return sorted(
        [p for p in project_dir.iterdir() if p.is_dir() and re.fullmatch(r"query\d+", p.name)],
        key=lambda p: int(re.search(r"\d+", p.name).group())
    )

def main():
    project_dir = Path(__file__).parent
    load_dotenv()

    # Load db description
    with open(project_dir / "db_description.txt") as f:
        db_description = f.read()

    # Load db config
    with open(project_dir / "db_config.yaml") as f:
        db_config = yaml.safe_load(f)

    # Init client
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY_o3"),
        api_version=os.getenv("AZURE_API_VERSION_o3", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE_o3")
    )

    deployment_name = "o3"

    queries = find_query_dirs(project_dir)
    print(f"📝 Found {len(queries)} queries: {[q.name for q in queries]}")

    successes = 0
    failures = 0

    for i, query_dir in enumerate(queries, 1):
        print(f"\n🚀 Running query {i}/{len(queries)}: {query_dir.name}")
        success = run_baseline_agent(
            query_dir=query_dir,
            project_dir=project_dir,
            db_description=db_description,
            db_config=db_config,
            client=client,
            deployment_name=deployment_name
        )
        if success:
            successes += 1
        else:
            failures += 1

    print(f"\n✅ Done. Successes: {successes}, Failures: {failures}")

if __name__ == "__main__":
    main()
