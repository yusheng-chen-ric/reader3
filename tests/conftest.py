"""
Pytest configuration and fixtures.
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Database, Flashcard, Deck, QAHistory
from reader3 import Book, BookMetadata, ChapterContent, TOCEntry


@pytest.fixture
def temp_db() -> Generator[Database, None, None]:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    yield db

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_deck(temp_db: Database) -> Deck:
    """Create a sample deck for testing."""
    deck = Deck(
        name="Test Deck",
        description="A test deck",
        book_id="test_book"
    )
    deck.id = temp_db.create_deck(deck)
    return deck


@pytest.fixture
def sample_flashcard(temp_db: Database, sample_deck: Deck) -> Flashcard:
    """Create a sample flashcard for testing."""
    card = Flashcard(
        deck_id=sample_deck.id,
        book_id="test_book",
        chapter_index=0,
        front="What is the capital of France?",
        back="Paris",
        card_type="basic"
    )
    card.id = temp_db.create_flashcard(card)
    return card


@pytest.fixture
def sample_book() -> Book:
    """Create a sample book for testing."""
    metadata = BookMetadata(
        title="Test Book",
        authors=["Test Author"],
        language="en",
        identifier="test-123"
    )

    chapter1 = ChapterContent(
        href="chapter1.html",
        order=0,
        content="<h1>Chapter 1</h1><p>This is the first chapter.</p>",
        plain_text="Chapter 1 This is the first chapter."
    )

    chapter2 = ChapterContent(
        href="chapter2.html",
        order=1,
        content="<h1>Chapter 2</h1><p>This is the second chapter.</p>",
        plain_text="Chapter 2 This is the second chapter."
    )

    toc = [
        TOCEntry(
            title="Chapter 1",
            file_href="chapter1.html",
            children=[]
        ),
        TOCEntry(
            title="Chapter 2",
            file_href="chapter2.html",
            children=[]
        )
    ]

    return Book(
        metadata=metadata,
        spine=[chapter1, chapter2],
        toc=toc,
        image_paths={}
    )


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    # Import here to avoid circular imports
    from server import app
    return TestClient(app)


@pytest.fixture
def mock_ai_provider(mocker):
    """Mock AI provider to avoid actual API calls."""
    mock_provider = mocker.MagicMock()

    async def mock_generate_completion(*args, **kwargs):
        return "This is a mock AI response."

    async def mock_generate_streaming(*args, **kwargs):
        yield "This "
        yield "is "
        yield "streaming."

    mock_provider.generate_completion = mock_generate_completion
    mock_provider.generate_streaming = mock_generate_streaming

    return mock_provider


@pytest.fixture
def sample_qa_history(temp_db: Database) -> QAHistory:
    """Create sample Q&A history for testing."""
    qa = QAHistory(
        book_id="test_book",
        chapter_index=0,
        question="What is this chapter about?",
        answer="This chapter introduces the main character.",
        context="Chapter 1 content..."
    )
    qa.id = temp_db.save_qa(qa)
    return qa


@pytest.fixture
def multiple_flashcards(temp_db: Database, sample_deck: Deck):
    """Create multiple flashcards with different states."""
    cards = []

    # New card
    new_card = Flashcard(
        deck_id=sample_deck.id,
        book_id="test_book",
        chapter_index=0,
        front="New card question?",
        back="New card answer",
        repetitions=0,
        interval=0
    )
    new_card.id = temp_db.create_flashcard(new_card)
    cards.append(new_card)

    # Learning card
    learning_card = Flashcard(
        deck_id=sample_deck.id,
        book_id="test_book",
        chapter_index=0,
        front="Learning card question?",
        back="Learning card answer",
        repetitions=1,
        interval=1,
        next_review=datetime.now() - timedelta(days=1)
    )
    learning_card.id = temp_db.create_flashcard(learning_card)
    cards.append(learning_card)

    # Due card
    due_card = Flashcard(
        deck_id=sample_deck.id,
        book_id="test_book",
        chapter_index=0,
        front="Due card question?",
        back="Due card answer",
        repetitions=3,
        interval=7,
        next_review=datetime.now() - timedelta(days=1)
    )
    due_card.id = temp_db.create_flashcard(due_card)
    cards.append(due_card)

    # Future card
    future_card = Flashcard(
        deck_id=sample_deck.id,
        book_id="test_book",
        chapter_index=0,
        front="Future card question?",
        back="Future card answer",
        repetitions=5,
        interval=30,
        next_review=datetime.now() + timedelta(days=10)
    )
    future_card.id = temp_db.create_flashcard(future_card)
    cards.append(future_card)

    return cards
