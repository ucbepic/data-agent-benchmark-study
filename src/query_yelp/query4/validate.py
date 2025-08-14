import re

def validate(llm_output: str) -> (bool, str):
    """
    Validate if ground truth 'Restaurant,3.63' is present in LLM output.
    - Category: ignore case
    - Value: match 2 decimal places

    Args:
        llm_output (str): text output from LLM

    Returns:
        (True, "OK") if found
        (False, reason) if not
    """
    gt_category = "Restaurant"
    gt_value = 3.633676092544987

    gt_category_lower = gt_category.lower()
    gt_value_str = f"{gt_value:.2f}"

    # 检查类别
    if gt_category_lower not in llm_output.lower():
        reason = f"Category '{gt_category}' not found in LLM output."
        print(f"❌ {reason}")
        return False, reason

    # 提取所有浮点数
    matches = re.findall(r"\d+\.\d+", llm_output)

    if not matches:
        reason = "No float number found in LLM output."
        print(f"❌ {reason}")
        return False, reason

    # 检查是否有匹配的数值
    for m in matches:
        if f"{float(m):.2f}" == gt_value_str:
            print(f"✅ Found: {gt_category}, {gt_value_str}")
            return True, "OK"

    reason = f"Value '{gt_value_str}' not found in LLM output."
    print(f"❌ {reason}")
    return False, reason
