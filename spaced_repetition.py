"""
SM-2 Spaced Repetition Algorithm implementation (used by Anki).

The SM-2 algorithm calculates the optimal review intervals for flashcards
based on how well you remember them.

Rating scale:
- 1 (Again): Complete blackout, incorrect response
- 2 (Hard): Correct response but with serious difficulty
- 3 (Good): Correct response with some hesitation
- 4 (Easy): Perfect response, easy recall
"""

from datetime import datetime, timedelta
from database import Flashcard


def calculate_next_review(card: Flashcard, rating: int) -> Flashcard:
    """
    Apply SM-2 algorithm to calculate the next review interval.

    Args:
        card: The flashcard to update
        rating: User rating (1=Again, 2=Hard, 3=Good, 4=Easy)

    Returns:
        Updated flashcard with new SM-2 parameters
    """
    card.last_review = datetime.now()
    card.total_reviews += 1

    # Rating 1 (Again) = Failed recall
    if rating == 1:
        card.repetitions = 0
        card.interval = 0
        card.lapses += 1
        # Reduce ease factor for failed cards
        card.ease_factor = max(1.3, card.ease_factor - 0.2)
        # Review again soon (1 minute in production, we'll use 1 day for simplicity)
        card.next_review = datetime.now() + timedelta(days=1)

    # Rating 2-4 (Hard, Good, Easy) = Successful recall
    else:
        card.repetitions += 1

        # Adjust ease factor based on rating
        if rating == 2:  # Hard
            card.ease_factor = max(1.3, card.ease_factor - 0.15)
        elif rating == 4:  # Easy
            card.ease_factor = min(2.5, card.ease_factor + 0.15)
        # Rating 3 (Good) keeps ease factor unchanged

        # Calculate interval based on repetition number
        if card.repetitions == 1:
            card.interval = 1  # First review: 1 day
        elif card.repetitions == 2:
            card.interval = 6  # Second review: 6 days
        else:
            # Subsequent reviews: multiply previous interval by ease factor
            card.interval = round(card.interval * card.ease_factor)

        # Apply rating modifiers to interval
        if rating == 2:  # Hard: shorter interval
            card.interval = max(1, round(card.interval * 1.2))
        elif rating == 4:  # Easy: longer interval
            card.interval = round(card.interval * 1.3)

        # Set next review date
        card.next_review = datetime.now() + timedelta(days=card.interval)

    return card


def get_review_intervals(card: Flashcard) -> dict:
    """
    Calculate what the intervals would be for each rating option.
    Useful for showing the user preview of next review times.

    Returns:
        Dict with keys 'again', 'hard', 'good', 'easy' containing timedelta objects
    """
    from copy import deepcopy

    intervals = {}

    for rating, label in [(1, 'again'), (2, 'hard'), (3, 'good'), (4, 'easy')]:
        temp_card = deepcopy(card)
        temp_card = calculate_next_review(temp_card, rating)

        if rating == 1:
            intervals[label] = timedelta(days=1)
        else:
            intervals[label] = timedelta(days=temp_card.interval)

    return intervals


def format_interval(td: timedelta) -> str:
    """
    Format a timedelta into a human-readable string.

    Examples:
        - 1 day → "1d"
        - 6 days → "6d"
        - 30 days → "1mo"
        - 365 days → "1yr"
    """
    days = td.days

    if days < 1:
        return "<1d"
    elif days == 1:
        return "1d"
    elif days < 30:
        return f"{days}d"
    elif days < 365:
        months = round(days / 30)
        return f"{months}mo"
    else:
        years = round(days / 365)
        return f"{years}yr"


def get_card_state(card: Flashcard) -> str:
    """
    Get the current state of the card.

    Returns:
        'new', 'learning', or 'review'
    """
    if card.repetitions == 0:
        return 'new'
    elif card.repetitions < 3:
        return 'learning'
    else:
        return 'review'


def is_card_due(card: Flashcard) -> bool:
    """Check if a card is due for review."""
    return card.next_review <= datetime.now()
