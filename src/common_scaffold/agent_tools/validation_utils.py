from pathlib import Path
from datetime import datetime
import importlib.util

def validate_and_log(query_dir: Path, llm_answer: str) -> tuple[bool, str]:
    """
    执行 query_dir/validate.py 校验 LLM 输出，并记录日志。

    Args:
        query_dir (Path): query 目录，例如 query_stockmarket/query2
        llm_answer (str): LLM 返回的答案

    Returns:
        (is_valid, reason): 校验是否通过，以及原因
    """
    # 调用 validate.py
    validate_py = query_dir / "validate.py"
    if not validate_py.exists():
        raise FileNotFoundError(f"❌ validate.py not found at: {validate_py}")

    spec = importlib.util.spec_from_file_location("validate", str(validate_py))
    validate_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validate_mod)

    is_valid, reason = validate_mod.validate(llm_answer)

    # 写日志
    write_validation_log(
        query_name=query_dir.name,
        llm_answer=llm_answer,
        match_result=is_valid,
        reason=reason
    )

    return is_valid, reason


def write_validation_log(query_name: str, llm_answer: str, match_result: bool, reason: str):
    """
    写 validation_log.txt
    """
    log_path = Path.cwd() / "validation_log.txt"
    gt_path = Path.cwd() / query_name / "ground_truth.csv"

    # 读 ground truth
    if not gt_path.exists():
        print(f"⚠️ ground_truth.csv not found: {gt_path}")
        gt_lines = ["<ground truth file missing>"]
    else:
        with open(gt_path, encoding="utf-8") as f:
            gt_lines = [line.strip() for line in f if line.strip()]

    gt_str = "\n".join(gt_lines)

    timestamp = datetime.now().isoformat(timespec="seconds")
    result_str = "✅ MATCH" if match_result else f"❌ MISMATCH: {reason}"

    log_lines = [
        f"=== Validation Log ({timestamp}) ===",
        f"Query: {query_name}",
        "",
        "LLM Answer:",
        llm_answer.strip(),
        "",
        "Ground Truth:",
        gt_str,
        "",
        f"Result: {result_str}",
        "="*80,
        ""
    ]
    log_entry = "\n".join(log_lines)

    if log_path.exists():
        old_content = log_path.read_text(encoding="utf-8")
    else:
        old_content = ""

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_entry + "\n" + old_content)

    print(f"\n📄 Validation log updated at: {log_path}")

def log_failed(query_dir: Path, reason: str):
    """
    when agent break down due to code issue
    """
    write_validation_log(
        query_name=query_dir.name,
        llm_answer="FAILED due to agent crash",
        match_result=False,
        reason=reason
    )
