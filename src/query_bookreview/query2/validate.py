def validate(llm_output: str) -> (bool, str):
    """
    Validate if all ground truth book titles are present in LLM output.
    Only checks book titles (ignores categories).
    Returns:
        (True, "OK") if all found
        (False, reason) if any missing
    """
    ground_truth_books = [
        "The Sludge",
        "Something That Feels Like Truth (Switchgrass Books)",
        "Kennebago Moments",
        "Hollywood Confessions: Hollywood Headlines Book #3 (Hollywood Headlines Mysteries)",
        "Forged in Blood (Freehold)",
        "Local Honey",
        "Exits, Desires, & Slow Fires",
        "Fire Cracker",
        "Reunion: The Children of Lauderdale Park",
        "Childe Harold of Dysna",
        "The Prophet: With Original 1923 Illustrations by the Author",
        "Knowing When To Die: Uncollected Stories",
        "Liza of Lambeth",
        "Child Of The King A Journey of Hope Book 1: Earthly Story With A Heavenly Message",
        "The Melancholy Strumpet Master"
    ]

    llm_lower = llm_output.lower()

    for book in ground_truth_books:
        if book.lower() not in llm_lower:
            reason = f"Missing book title in LLM output: {book}"
            print(f"❌ {reason}")
            return False, reason

    print("✅ All book titles found in LLM output.")
    return True, "OK"
