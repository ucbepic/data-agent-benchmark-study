import re

def levenshtein(s1: str, s2: str) -> int:
    """
    Compute Levenshtein edit distance between two strings.
    """
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def validate(llm_output: str) -> (bool, str):
    """
    Validate:
    - all gt names are present (case-insensitive, exact or ≤5 edits, dynamic window)

    Returns:
        (True, "OK") if all pass
        (False, reason) if not
    """
    ground_truth_names = [
        "Synthesis Energy Systems, Inc",
        "TD Holdings, Inc",
        "TMSR Holding Company Limited",
        "Verb Technology Company, Inc",
        "Sunesis Pharmaceuticals, Inc",
    ]

    llm_output_clean = re.sub(r'\s+', ' ', llm_output).strip().lower()

    for gt_name in ground_truth_names:
        gt_name_clean = gt_name.lower()
        name_len = len(gt_name_clean)

        # exact
        if gt_name_clean in llm_output_clean:
            print(f"✅ Exact match: {gt_name}")
            continue

        # fuzzy
        min_distance = float('inf')
        best_match = ""
        window_range = 10

        for i in range(len(llm_output_clean) - name_len + 1):
            for extra in range(-window_range, window_range + 1):
                start = i
                end = i + name_len + extra
                if end > len(llm_output_clean) or end <= start:
                    continue

                candidate = llm_output_clean[start:end]
                candidate = re.sub(r'\b\d+([.,]\d+)?\b', '', candidate)
                candidate = re.sub(r'\s+', ' ', candidate).strip()
                if not candidate:
                    continue

                dist = levenshtein(gt_name_clean, candidate)
                if dist < min_distance:
                    min_distance = dist
                    best_match = candidate
                    if min_distance == 0:
                        break
            if min_distance == 0:
                break

        if min_distance <= 5:
            print(f"⚠️ Fuzzy match: GT='{gt_name}' ↔ LLM='{best_match}' (distance={min_distance})")
        else:
            reason = f"❌ Name not found within 5 edits: '{gt_name}', closest: '{best_match}' (distance={min_distance})"
            print(reason)
            return False, reason

    print("✅ All names (exact or ≤5 edits) matched.")
    return True, "OK"