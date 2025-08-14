import re
import sys
import numpy as np
import pandas as pd
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common_scaffold.agent_tools import run_baseline_agent


def find_query_dirs(project_dir: Path):
    """Find all queryN directories sorted by N"""
    return sorted(
        [p for p in project_dir.iterdir() if p.is_dir() and re.fullmatch(r"query\d+", p.name)],
        key=lambda p: int(re.search(r"\d+", p.name).group())
    )


def pass_at_k(n, c, k):
    """Compute unbiased pass@k"""
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, default=None,
                        help="query_id (e.g. query3) to start from; default is from the beginning")
    args = parser.parse_args()

    # Configurable parameters
    n = 50
    k_list = [1, 5, 10, 15, 20, 30, 40, 50]

    project_dir = Path(__file__).parent
    load_dotenv()

    # Load DB description & config
    with open(project_dir / "db_description.txt") as f:
        db_description = f.read()
    with open(project_dir / "db_config.yaml") as f:
        db_config = yaml.safe_load(f)

    client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY_o3"),
        api_version=os.getenv("AZURE_API_VERSION_o3", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE_o3")
    )
    deployment_name = "gpt-4.1"

    queries = find_query_dirs(project_dir)
    query_names = [q.name for q in queries]

    # load existing results if any
    result_path = project_dir / "pass_at_k_results_nh_gpt-4.1.csv"
    if result_path.exists():
        df_existing = pd.read_csv(result_path)
        done_queries = set(df_existing["query_id"].dropna().tolist())
    else:
        df_existing = pd.DataFrame()
        done_queries = set()

    # decide where to start
    start_idx = 0
    if args.start:
        if args.start in query_names:
            start_idx = query_names.index(args.start)
        else:
            print(f"❌ Invalid start query_id: {args.start}")
            sys.exit(1)

    print(f"📝 Found {len(queries)} queries: {query_names}")
    print(f"🚀 Starting from: {query_names[start_idx]}")
    print(f"✅ Already done: {done_queries}")

    all_rows = []

    for i, query_dir in enumerate(queries[start_idx:], start=start_idx + 1):
        qid = query_dir.name
        if qid in done_queries:
            print(f"⏩ Skipping already done: {qid}")
            continue

        print(f"\n🚀 Query {i}/{len(queries)}: {qid}")
        c = 0

        for run_id in range(1, n + 1):
            print(f"   ▶ Run {run_id}/{n}")
            print(f"🧠 Using model deployment: {deployment_name}")
            success = run_baseline_agent(
                query_dir=query_dir,
                project_dir=project_dir,
                db_description=db_description,
                db_config=db_config,
                client=client,
                deployment_name=deployment_name
            )
            if success:
                c += 1

        row = {"query_id": qid, "n": n, "c": c}
        print(f"✅ {qid}: {c}/{n} correct")

        for k in k_list:
            passk = pass_at_k(n, c, k)
            row[f"pass@{k}"] = passk
            print(f"🎯 {qid} pass@{k}: {passk:.4f}")

        all_rows.append(row)

        # save intermediate results
        df_new = pd.DataFrame(all_rows)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(result_path, index=False)
        print(f"💾 Saved intermediate results to: {result_path}")

        # reset new rows for next query
        df_existing = df_combined.copy()
        all_rows = []

    # compute overall and save
    if not df_existing.empty:
        overall_row = {"query_id": "Overall"}
        for k in k_list:
            overall_row[f"pass@{k}"] = df_existing[f"pass@{k}"].mean()
        df_final = pd.concat([df_existing, pd.DataFrame([overall_row])], ignore_index=True)
        df_final.to_csv(result_path, index=False)
        print(f"\n🌟 Final results (with Overall) saved to: {result_path}")

if __name__ == "__main__":
    main()
