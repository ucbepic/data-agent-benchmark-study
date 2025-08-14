def validate(llm_output: str) -> (bool, str):
    """
    Validate that all ground truth project names appear in LLM output.
    
    Rules:
    - Project names must be found in the output (case-insensitive)
    - Order and exact formatting do not matter

    Returns:
        (True, "OK") if all found
        (False, reason) if any missing
    """
    ground_truth_projects = [
        "mui-org/material-ui",
        "moment/moment",
        "semantic-org/semantic-ui",
        "react-native-elements/react-native-elements",
        "sveltejs/svelte",
    ]

    llm_output_lower = llm_output.lower()

    for project in ground_truth_projects:
        if project.lower() not in llm_output_lower:
            reason = f"Missing project name: {project}"
            print(f"❌ {reason}")
            return False, reason

    print("✅ All project names found.")
    return True, "OK"
