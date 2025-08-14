import pandas as pd
import json
from typing import Any

def format_preview(result: Any, max_len: int = 9500) -> str:
    """
    Format a result object into a readable string preview, truncated to max_len.

    Args:
        result (Any): The result to format (DataFrame, dict, list, str, etc.)
        max_len (int): Maximum length of the preview string.

    Returns:
        str: Formatted preview string.
    """
    try:
        if isinstance(result, pd.DataFrame):
            preview = result.head(100).to_markdown()
        elif isinstance(result, (dict, list)):
            preview = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            preview = str(result)
    except Exception as e:
        preview = f"[Preview formatting error: {type(e).__name__}: {e}]"


    if len(preview) > max_len:
        preview = preview[:max_len] + "\n... (truncated)"

    return preview
