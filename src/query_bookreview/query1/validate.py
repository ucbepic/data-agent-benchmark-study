def validate(llm_output: str) -> (bool, str):
    """
    Validate if ground truth '2020' is present in LLM output.
    Returns:
        (True, "OK") if found
        (False, reason) if not
    """
    gt = "2020"

    if gt in llm_output:
        print("✅ Ground truth found in LLM output.")
        return True, "OK"
    else:
        reason = f"Ground truth '{gt}' not found in LLM output."
        print(f"❌ {reason}")
        return False, reason
