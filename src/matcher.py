from rapidfuzz import process, fuzz

def match_string(query: str, choices: list[str], cutoff: float = 60.0):
    """
    Finds the best fuzzy match for a query string within a list of choices.
    
    Args:
        query: The string to match (e.g., raw OCR text).
        choices: List of candidate strings (e.g., Warframe Market item list).
        cutoff: Minimum match score (0-100) to accept a match.
        
    Returns:
        tuple: (best_match_string, confidence_score) or (None, best_score)
    """
    if not query or not choices:
        return None, 0.0

    # extractOne returns a tuple: (matched_choice, score, index)
    match, score, _ = process.extractOne(
        query,
        choices,
        scorer=fuzz.token_sort_ratio
    )

    if score >= cutoff:
        return match, score
    
    return None, score


# ==========================================
# Example Usage & Verification
# ==========================================
if __name__ == "__main__":
    # Simulated item list from API
    item_list = [
        "Sevagoth Prime Neuroptics Blueprint",
        "Forma Blueprint",
        "Braton Prime Blueprint",
        "Soma Prime Barrel",
        "Soma Prime Stock"
    ]

    # Raw OCR outputs with typos and noise
    ocr_outputs = [
        "Sevagoih&rime Neuroptics Blueprint",
        "Forma Blueprint",
        "Braton Prim Blueprint",
        "Some Prime Barrel"
    ]

    print(f"{'OCR Input':<40} -> {'Matched Item':<38} | {'Score'}")
    print("-" * 88)

    for ocr in ocr_outputs:
        matched_item, score = match_string(ocr, item_list)
        print(f"{ocr:<40} -> {str(matched_item):<38} | {score:.1f}%")