import json
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common_scaffold.agent_tools import run_baseline_agent

query_dir = Path(__file__).parent / "query1"
deployment_name = "o3"

load_dotenv()

with open(query_dir / "query.json") as f:
    query_content = json.load(f)

if isinstance(query_content, str):
    user_query = query_content
elif isinstance(query_content, dict) and "query" in query_content:
    user_query = query_content["query"]
else:
    raise ValueError("query.json wrong format")

with open("db_description.txt") as f:
    db_description = f.read()

project_dir = Path(__file__).parent
with open(project_dir / "db_config.yaml") as f:
    db_config = yaml.safe_load(f)
db_clients = db_config["db_clients"]




client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY_o3"),
    api_version=os.getenv("AZURE_API_VERSION_o3", "2023-05-15"),
    azure_endpoint=os.getenv("AZURE_API_BASE_o3")
)



if __name__ == "__main__":
    success = run_baseline_agent(
        query_dir=query_dir,
        project_dir=project_dir,
        db_description=db_description,
        db_config=db_config,
        client=client,
        deployment_name="o3"
    )
    print("✅ Test completed" if success else "❌ Test failed")