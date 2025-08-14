import re

# Ground truth (Name, Version)
gt_pairs = [
    ("@dmrvos/infrajs>0.0.6>typescript", "2.6.2"),
    ("@dmrvos/infrajs>0.0.5>typescript", "2.6.2"),
    ("@dylanvann/svelte", "3.25.4"),
    ("@dumc11/tailwindcss", "0.4.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.indexof", "4.0.5"),
]

def validate(llm_output: str) -> (bool, str):
    """
    Validate:
    - Each name in ground truth appears in LLM output (case-insensitive)
    - The corresponding version appears in the 50 characters *after* the name (excluding the name itself)

    Returns:
        (True, "OK") if all match
        (False, reason) otherwise
    """
    llm_lower = llm_output.lower()

    for name, version in gt_pairs:
        name_lower = name.lower()
        idx = llm_lower.find(name_lower)

        if idx == -1:
            reason = f"Missing name: {name}"
            print(f"❌ {reason}")
            return False, reason

        # Only check in the 50 characters *after* the name
        start = idx + len(name_lower)
        window = llm_lower[start: start + 10]

        if version.lower() not in window:
            reason = f"Version '{version}' not found after name '{name}'"
            print(f"❌ {reason}")
            return False, reason

        print(f"✅ Matched name + version: {name} → {version}")

    print("✅ All name-version pairs validated successfully.")
    return True, "OK"
