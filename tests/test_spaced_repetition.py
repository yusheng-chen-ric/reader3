"""
Unit tests for spaced repetition (SM-2 algorithm).
"""

import pytest
from datetime import datetime, timedelta

from database import Flashcard
from spaced_repetition import (
    calculate_next_review,
    get_review_intervals,
    format_interval,
    get_card_state,
    is_card_due
)


@pytest.mark.unit
class TestSM2Algorithm:
    """Test SM-2 spaced repetition algorithm."""

    def test_again_rating_resets_card(self):
        """Test that rating 1 (Again) resets the card."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            repetitions=5,
            interval=30,
            ease_factor=2.5
        )

        updated = calculate_next_review(card, rating=1)

        assert updated.repetitions == 0
        assert updated.interval == 0
        assert updated.ease_factor < 2.5  # Ease decreased
        assert updated.lapses == 1

    def test_first_successful_review(self):
        """Test first successful review (rating 3)."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            repetitions=0,
            interval=0
        )

        updated = calculate_next_review(card, rating=3)

        assert updated.repetitions == 1
        assert updated.interval == 1  # First review: 1 day

    def test_second_successful_review(self):
        """Test second successful review."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            repetitions=1,
            interval=1
        )

        updated = calculate_next_review(card, rating=3)

        assert updated.repetitions == 2
        assert updated.interval == 6  # Second review: 6 days

    def test_subsequent_reviews(self):
        """Test subsequent reviews multiply by ease factor."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            repetitions=2,
            interval=6,
            ease_factor=2.5
        )

        updated = calculate_next_review(card, rating=3)

        assert updated.repetitions == 3
        assert updated.interval == round(6 * 2.5)  # Multiply by ease

    def test_hard_rating_decreases_ease(self):
        """Test that rating 2 (Hard) decreases ease factor."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            ease_factor=2.5
        )

        updated = calculate_next_review(card, rating=2)

        assert updated.ease_factor < 2.5

    def test_easy_rating_increases_ease(self):
        """Test that rating 4 (Easy) increases ease factor."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            ease_factor=2.0
        )

        updated = calculate_next_review(card, rating=4)

        assert updated.ease_factor > 2.0

    def test_ease_factor_bounds(self):
        """Test that ease factor stays within bounds."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            ease_factor=1.3  # Already at minimum
        )

        # Try to decrease further
        updated = calculate_next_review(card, rating=1)
        assert updated.ease_factor >= 1.3

        # Test maximum
        card.ease_factor = 2.5
        updated = calculate_next_review(card, rating=4)
        assert updated.ease_factor <= 2.5

    def test_review_updates_timestamps(self):
        """Test that reviews update last_review and next_review."""
        card = Flashcard(
            front="Question?",
            back="Answer"
        )

        before = datetime.now()
        updated = calculate_next_review(card, rating=3)
        after = datetime.now()

        assert updated.last_review >= before
        assert updated.last_review <= after
        assert updated.next_review > before

    def test_total_reviews_incremented(self):
        """Test that total_reviews is incremented."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            total_reviews=5
        )

        updated = calculate_next_review(card, rating=3)
        assert updated.total_reviews == 6


@pytest.mark.unit
class TestReviewIntervals:
    """Test interval calculations and previews."""

    def test_get_review_intervals(self):
        """Test getting preview of intervals for all ratings."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            repetitions=3,
            interval=7
        )

        intervals = get_review_intervals(card)

        assert 'again' in intervals
        assert 'hard' in intervals
        assert 'good' in intervals
        assert 'easy' in intervals

        # Again should be shortest
        assert intervals['again'].days < intervals['good'].days

        # Easy should be longest
        assert intervals['easy'].days > intervals['good'].days

    def test_format_interval_days(self):
        """Test formatting intervals in days."""
        assert format_interval(timedelta(days=1)) == "1d"
        assert format_interval(timedelta(days=5)) == "5d"

    def test_format_interval_months(self):
        """Test formatting intervals in months."""
        assert format_interval(timedelta(days=30)) == "1mo"
        assert format_interval(timedelta(days=60)) == "2mo"

    def test_format_interval_years(self):
        """Test formatting intervals in years."""
        assert format_interval(timedelta(days=365)) == "1yr"
        assert format_interval(timedelta(days=730)) == "2yr"

    def test_format_interval_less_than_day(self):
        """Test formatting intervals less than a day."""
        assert format_interval(timedelta(hours=12)) == "<1d"


@pytest.mark.unit
class TestCardState:
    """Test card state determination."""

    def test_new_card_state(self):
        """Test identifying new cards."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            repetitions=0
        )

        assert get_card_state(card) == 'new'

    def test_learning_card_state(self):
        """Test identifying learning cards."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            repetitions=1
        )

        assert get_card_state(card) == 'learning'

        card.repetitions = 2
        assert get_card_state(card) == 'learning'

    def test_review_card_state(self):
        """Test identifying review cards."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            repetitions=3
        )

        assert get_card_state(card) == 'review'

    def test_is_card_due_past(self):
        """Test card is due when next_review is in the past."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            next_review=datetime.now() - timedelta(days=1)
        )

        assert is_card_due(card) is True

    def test_is_card_due_now(self):
        """Test card is due when next_review is now."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            next_review=datetime.now()
        )

        assert is_card_due(card) is True

    def test_is_card_not_due(self):
        """Test card is not due when next_review is in the future."""
        card = Flashcard(
            front="Question?",
            back="Answer",
            next_review=datetime.now() + timedelta(days=1)
        )

        assert is_card_due(card) is False
