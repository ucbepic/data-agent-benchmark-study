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
    Validate that:
    - All GT names appear in LLM output (case-insensitive, ≤5 edit distance allowed)
    - For each name, a number appears nearby (within 50 chars after name)
    - Both GT and LLM numbers are rounded to nearest integer before comparison

    Returns:
        (True, "OK") if all pass
        (False, reason) if not
    """
    gt_pairs = [
        ("Apex Global Brands Inc", 23781.42),
        ("BIO-key International, Inc", 10988.14),
        ("CBAK Energy Technology, Inc", 86223.32),
        ("China Ceramics Co, Ltd", 4366.80),
        ("Correvio Pharma Corp", 145247.83),
        ("CounterPath Corporation", 375.49),
        ("DASAN Zhone Solutions, Inc", 15578.66),
        ("Future FinTech Group Inc", 9.85),
        ("Frontier Communications Corporation", 254397.63),
        ("Ideanomics, Inc", 10.28),
        ("Ocean Power Technologies, Inc", 254.15),
        ("Pacific Ethanol, Inc", 10706.72),
        ("Synthesis Energy Systems, Inc", 2390.51),
        ("Sunesis Pharmaceuticals, Inc", 781.82),
        ("Sypris Solutions, Inc", 36836.36),
    ]

    llm_output_clean = re.sub(r'\s+', ' ', llm_output).strip().lower()

    for name, value in gt_pairs:
        name_clean = name.lower()
        name_len = len(name_clean)

        idx = llm_output_clean.find(name_clean)

        if idx != -1:
            print(f"✅ Exact match: {name}")
            best_match = name_clean
            match_len = name_len
            min_distance = 0
        else:
            # fuzzy match
            min_distance = float('inf')
            best_match = ""
            best_idx = -1
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

                    dist = levenshtein(name_clean, candidate)
                    if dist < min_distance:
                        min_distance = dist
                        best_match = candidate
                        best_idx = start
                        if min_distance == 0:
                            break
                if min_distance == 0:
                    break

            if min_distance <= 5:
                print(f"⚠️ Fuzzy match: GT='{name}' ↔ LLM='{best_match}' (distance={min_distance})")
                idx = best_idx
                match_len = len(best_match)
            else:
                reason = f"❌ Name not found within 5 edits: '{name}', closest: '{best_match}' (distance={min_distance})"
                print(reason)
                return False, reason

        # unified window based on match_len
        window = llm_output_clean[idx: idx + match_len + 50]
        matches = re.findall(r"\d+(?:\.\d+)?", window)

        if not matches:
            reason = f"No number found near name: {name}"
            print(f"❌ {reason}")
            return False, reason

        expected_rounded = round(value)
        found_match = False

        for m in matches:
            try:
                val_rounded = round(float(m))
                if val_rounded == expected_rounded:
                    found_match = True
                    break
            except Exception:
                continue

        if not found_match:
            reason = f"Number near '{name}' does not match rounded {expected_rounded}"
            print(f"❌ {reason}")
            return False, reason

    print("✅ All names (exact or ≤5 edits) and rounded numbers matched.")
    return True, "OK"

