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
    - number 31 is present somewhere in LLM output
    - all gt names are present (exact or <=5 edits, case-insensitive, dynamic window)
    """
    ground_truth_names = [
        "ProShares Ultra Bloomberg Natural Gas",
        "ProShares UltraShort MSCI Brazil Capped",
        "Direxion Auspice Broad Commodity Strategy ETF",
        "Direxion Daily Gold Miners Index Bear 2X Shares",
        "Direxion Emerging Markets Bear 3X Shares",
        "Direxion Energy Bull 2X Shares",
        "Direxion Financial Bear 3X Shares",
        "ProShares Ultrashort FTSE China 50",
        "Goldman Sachs Motif Finance Reimagined ETF",
        "Direxion Daily S&P Oil & Gas Exp. & Prod. Bull 2X Shares",
        "Xtrackers High Beta High Yield Bond ETF",
        "Direxion Daily Junior Gold Miners Index Bear 2X Shares",
        "Direxion Daily Junior Gold Miners Index Bull 2X Shares",
        "Xtrackers Japan JPX-Nikkei 400 Equity ETF",
        "Direxion Daily S&P Biotech Bear 3X Shares",
        "Direxion Daily S&P Biotech Bull 3X Shares",
        "Direxion Daily Latin America 3x Bull Shares",
        "SPDR MidCap Trust Series I",
        "Pacer Trendpilot International ETF",
        "Pacer Benchmark Retail Real Estate SCTR ETF",
        "UltraPro Short Dow30",
        "Direxion Daily Semiconductor Bear 3x Shares",
        "ProShares UltraShort Semiconductors",
        "Direxion Technology Bear 3X Shares",
        "Direxion Small Cap Bear 3X Shares",
        "ProShares Trust Ultra VIX Short Term Futures ETF",
        "ProShares Trust VIX Short-Term Futures ETF",
        "Virtus Private Credit Strategy ETF",
        "SPDR Series Trust SPDR S&P Oil & Gas Equipment & Services ETF",
        "SPDR S&P Oil & Gas Explor & Product",
        "Direxion Daily FTSE China Bear 3x Shares",
    ]

    llm_output_clean = re.sub(r'\s+', ' ', llm_output).strip().lower()

    # check 31
    matches = re.findall(r"\b\d+\b", llm_output)
    if not any(int(m) == 31 for m in matches):
        reason = "Missing number: 31"
        print(f"❌ {reason}")
        return False, reason

    # check names
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

    print("✅ Number 31 and all names (exact or ≤5 edits) found.")
    return True, "OK"