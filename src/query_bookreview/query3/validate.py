def validate(llm_output: str) -> (bool, str):
    """
    Validate if all ground truth book titles are present in LLM output.
    Only checks book titles (ignores categories).
    Returns:
        (True, "OK") if all found
        (False, reason) if any missing
    """
    ground_truth_books = [
        "Around the World Mazes",
        "Behind the Wheel (Choose Your Own Adventure #35)(Paperback/Revised)",
        "Benny Goes To The Moon: The great new book from Top Children's entertainer Gerry Ogilvie (1)",
        "Cheer Up, Ben Franklin! (Young Historians)",
        "Favorite Thorton W. Burgess Stories: 6 Books",
        "Egypt (Enchantment of the World)",
        "Pokémon: Sun & Moon, Vol. 8 (8)",
        "The Library Book",
        "LunaLu the Llamacorn",
        "Monstrous Stories #4: The Day the Mice Stood Still",
        "The Old Man and the Pirate Princess",
        "Trouble in the CTC!: The Terra Prime Adventures Book 2",
        "Clark the Shark: Tooth Trouble, No. 1",
        "Cleo Porter and the Body Electric"
    ]

    llm_lower = llm_output.lower()

    for book in ground_truth_books:
        if book.lower() not in llm_lower:
            reason = f"Missing book title in LLM output: {book}"
            print(f"❌ {reason}")
            return False, reason

    print("✅ All book titles found in LLM output.")
    return True, "OK"
