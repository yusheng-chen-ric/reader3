"""
Unit tests for database operations.
"""

import pytest
from datetime import datetime, timedelta

from database import Database, Flashcard, Deck, QAHistory, ReviewLog


@pytest.mark.unit
class TestDatabase:
    """Test database initialization and basic operations."""

    def test_database_init(self, temp_db):
        """Test database initialization creates tables."""
        conn = temp_db.get_connection()
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('decks', 'flashcards', 'qa_history', 'review_log')
        """)
        tables = {row[0] for row in cursor.fetchall()}

        assert 'decks' in tables
        assert 'flashcards' in tables
        assert 'qa_history' in tables
        assert 'review_log' in tables

        conn.close()


@pytest.mark.unit
class TestDeckOperations:
    """Test deck CRUD operations."""

    def test_create_deck(self, temp_db):
        """Test creating a new deck."""
        deck = Deck(
            name="My Deck",
            description="Test deck",
            book_id="book1"
        )

        deck_id = temp_db.create_deck(deck)
        assert deck_id > 0

    def test_get_deck(self, temp_db, sample_deck):
        """Test retrieving a deck by ID."""
        retrieved = temp_db.get_deck(sample_deck.id)

        assert retrieved is not None
        assert retrieved.id == sample_deck.id
        assert retrieved.name == sample_deck.name
        assert retrieved.description == sample_deck.description

    def test_get_nonexistent_deck(self, temp_db):
        """Test getting a deck that doesn't exist."""
        result = temp_db.get_deck(99999)
        assert result is None

    def test_get_all_decks(self, temp_db):
        """Test getting all decks."""
        # Create multiple decks
        for i in range(3):
            deck = Deck(name=f"Deck {i}", book_id=f"book{i}")
            temp_db.create_deck(deck)

        decks = temp_db.get_all_decks()
        assert len(decks) == 3

    def test_get_or_create_book_deck(self, temp_db):
        """Test getting or creating a deck for a book."""
        book_id = "dracula"
        book_title = "Dracula"

        # First call creates
        deck_id1 = temp_db.get_or_create_book_deck(book_id, book_title)
        assert deck_id1 > 0

        # Second call returns same ID
        deck_id2 = temp_db.get_or_create_book_deck(book_id, book_title)
        assert deck_id1 == deck_id2


@pytest.mark.unit
class TestFlashcardOperations:
    """Test flashcard CRUD operations."""

    def test_create_flashcard(self, temp_db, sample_deck):
        """Test creating a flashcard."""
        card = Flashcard(
            deck_id=sample_deck.id,
            book_id="test_book",
            chapter_index=0,
            front="Question?",
            back="Answer",
            card_type="basic"
        )

        card_id = temp_db.create_flashcard(card)
        assert card_id > 0

    def test_get_flashcard(self, temp_db, sample_flashcard):
        """Test retrieving a flashcard."""
        retrieved = temp_db.get_flashcard(sample_flashcard.id)

        assert retrieved is not None
        assert retrieved.id == sample_flashcard.id
        assert retrieved.front == sample_flashcard.front
        assert retrieved.back == sample_flashcard.back

    def test_update_flashcard(self, temp_db, sample_flashcard):
        """Test updating a flashcard."""
        sample_flashcard.front = "Updated question?"
        sample_flashcard.back = "Updated answer"
        sample_flashcard.ease_factor = 2.0

        temp_db.update_flashcard(sample_flashcard)

        retrieved = temp_db.get_flashcard(sample_flashcard.id)
        assert retrieved.front == "Updated question?"
        assert retrieved.back == "Updated answer"
        assert retrieved.ease_factor == 2.0

    def test_delete_flashcard(self, temp_db, sample_flashcard):
        """Test deleting a flashcard."""
        card_id = sample_flashcard.id

        temp_db.delete_flashcard(card_id)

        retrieved = temp_db.get_flashcard(card_id)
        assert retrieved is None

    def test_get_cards_by_deck(self, temp_db, sample_deck):
        """Test getting all cards in a deck."""
        # Create multiple cards
        for i in range(3):
            card = Flashcard(
                deck_id=sample_deck.id,
                book_id="test_book",
                front=f"Question {i}?",
                back=f"Answer {i}"
            )
            temp_db.create_flashcard(card)

        cards = temp_db.get_cards_by_deck(sample_deck.id)
        assert len(cards) == 3

    def test_get_cards_due_for_review(self, temp_db, multiple_flashcards):
        """Test getting cards due for review."""
        due_cards = temp_db.get_cards_due_for_review()

        # Should return new, learning, and due cards (not future)
        assert len(due_cards) >= 3

    def test_deck_stats(self, temp_db, sample_deck, multiple_flashcards):
        """Test getting deck statistics."""
        stats = temp_db.get_deck_stats(sample_deck.id)

        assert stats['total'] == 4
        assert stats['new'] == 1
        assert stats['due'] == 2  # learning + due
        assert stats['learning'] == 1  # future


@pytest.mark.unit
class TestQAOperations:
    """Test Q&A history operations."""

    def test_save_qa(self, temp_db):
        """Test saving Q&A interaction."""
        qa = QAHistory(
            book_id="test_book",
            chapter_index=0,
            question="What happens in this chapter?",
            answer="The main character is introduced.",
            context="Chapter text..."
        )

        qa_id = temp_db.save_qa(qa)
        assert qa_id > 0

    def test_get_qa_history_by_book(self, temp_db):
        """Test getting Q&A history for a book."""
        book_id = "test_book"

        # Create multiple Q&As
        for i in range(3):
            qa = QAHistory(
                book_id=book_id,
                chapter_index=i,
                question=f"Question {i}?",
                answer=f"Answer {i}"
            )
            temp_db.save_qa(qa)

        history = temp_db.get_qa_history(book_id)
        assert len(history) == 3

    def test_get_qa_history_by_chapter(self, temp_db):
        """Test getting Q&A history for a specific chapter."""
        book_id = "test_book"
        chapter_index = 1

        # Create Q&As for different chapters
        for i in range(3):
            qa = QAHistory(
                book_id=book_id,
                chapter_index=i,
                question=f"Question {i}?",
                answer=f"Answer {i}"
            )
            temp_db.save_qa(qa)

        history = temp_db.get_qa_history(book_id, chapter_index)
        assert len(history) == 1
        assert history[0].chapter_index == chapter_index


@pytest.mark.unit
class TestReviewLog:
    """Test review logging."""

    def test_log_review(self, temp_db, sample_flashcard):
        """Test logging a card review."""
        log = ReviewLog(
            card_id=sample_flashcard.id,
            rating=3,
            time_taken=10
        )

        log_id = temp_db.log_review(log)
        assert log_id > 0
