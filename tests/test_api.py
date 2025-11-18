"""
Integration tests for API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch

from database import Flashcard, Deck


@pytest.mark.integration
class TestFlashcardAPI:
    """Test flashcard API endpoints."""

    @patch('server.get_ai_service')
    def test_generate_flashcards(self, mock_get_ai, test_client, temp_db, mocker):
        """Test generating flashcards via API."""
        # Mock AI service
        mock_service = mocker.MagicMock()
        mock_service.generate_flashcards = AsyncMock(return_value=[
            {"front": "Q1?", "back": "A1"},
            {"front": "Q2?", "back": "A2"}
        ])
        mock_get_ai.return_value = mock_service

        # Mock book loading
        with patch('server.load_book_cached') as mock_load:
            from conftest import sample_book
            mock_load.return_value = sample_book()

            response = test_client.post("/api/generate-flashcards", json={
                "book_id": "test_book",
                "chapter_index": 0,
                "selected_text": "This is a test passage about important concepts.",
                "num_cards": 2,
                "card_type": "basic"
            })

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['cards']) == 2

    @patch('server.get_ai_service')
    def test_ask_question(self, mock_get_ai, test_client, temp_db, mocker):
        """Test asking a question via API."""
        # Mock AI service
        mock_service = mocker.MagicMock()
        mock_service.answer_question = AsyncMock(
            return_value="This is the AI's answer to your question."
        )
        mock_get_ai.return_value = mock_service

        # Mock book loading
        with patch('server.load_book_cached') as mock_load:
            from conftest import sample_book
            mock_load.return_value = sample_book()

            response = test_client.post("/api/ask-question", json={
                "book_id": "test_book",
                "chapter_index": 0,
                "question": "What is this chapter about?",
                "context": "Chapter 1 content..."
            })

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'answer' in data

    def test_get_decks(self, test_client, temp_db):
        """Test getting all decks."""
        # Create test decks
        with patch('server.db', temp_db):
            deck1 = Deck(name="Deck 1", book_id="book1")
            deck1.id = temp_db.create_deck(deck1)

            deck2 = Deck(name="Deck 2", book_id="book2")
            deck2.id = temp_db.create_deck(deck2)

            response = test_client.get("/api/decks")

        assert response.status_code == 200
        data = response.json()
        assert 'decks' in data
        assert len(data['decks']) >= 2

    def test_get_deck_cards(self, test_client, temp_db, sample_deck):
        """Test getting cards in a deck."""
        with patch('server.db', temp_db):
            # Create some cards
            for i in range(3):
                card = Flashcard(
                    deck_id=sample_deck.id,
                    book_id="test_book",
                    front=f"Question {i}?",
                    back=f"Answer {i}"
                )
                temp_db.create_flashcard(card)

            response = test_client.get(f"/api/decks/{sample_deck.id}/cards")

        assert response.status_code == 200
        data = response.json()
        assert 'cards' in data
        assert len(data['cards']) == 3

    def test_get_due_cards(self, test_client, temp_db, multiple_flashcards):
        """Test getting cards due for review."""
        with patch('server.db', temp_db):
            response = test_client.get("/api/cards/due?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert 'cards' in data
        assert data['count'] >= 3  # new, learning, and due cards

    def test_review_card(self, test_client, temp_db, sample_flashcard):
        """Test reviewing a card."""
        with patch('server.db', temp_db):
            response = test_client.post(
                f"/api/cards/{sample_flashcard.id}/review",
                json={"rating": 3}
            )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'card' in data
        assert 'next_intervals' in data

    def test_review_card_invalid_rating(self, test_client, temp_db, sample_flashcard):
        """Test reviewing with invalid rating."""
        with patch('server.db', temp_db):
            response = test_client.post(
                f"/api/cards/{sample_flashcard.id}/review",
                json={"rating": 5}  # Invalid: must be 1-4
            )

        assert response.status_code == 400

    def test_update_card(self, test_client, temp_db, sample_flashcard):
        """Test updating a flashcard."""
        with patch('server.db', temp_db):
            response = test_client.put(
                f"/api/cards/{sample_flashcard.id}",
                json={
                    "front": "Updated question?",
                    "back": "Updated answer"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        # Verify update
        with patch('server.db', temp_db):
            updated = temp_db.get_flashcard(sample_flashcard.id)
            assert updated.front == "Updated question?"

    def test_delete_card(self, test_client, temp_db, sample_flashcard):
        """Test deleting a flashcard."""
        card_id = sample_flashcard.id

        with patch('server.db', temp_db):
            response = test_client.delete(f"/api/cards/{card_id}")

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        # Verify deletion
        with patch('server.db', temp_db):
            deleted = temp_db.get_flashcard(card_id)
            assert deleted is None

    def test_get_qa_history(self, test_client, temp_db, sample_qa_history):
        """Test getting Q&A history."""
        with patch('server.db', temp_db):
            response = test_client.get(
                f"/api/qa-history/{sample_qa_history.book_id}"
            )

        assert response.status_code == 200
        data = response.json()
        assert 'history' in data
        assert len(data['history']) >= 1


@pytest.mark.integration
class TestPageRoutes:
    """Test HTML page routes."""

    def test_library_page(self, test_client):
        """Test library page loads."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.content

    def test_decks_page(self, test_client):
        """Test decks page loads."""
        response = test_client.get("/decks")
        assert response.status_code == 200
        assert b"Flashcard Decks" in response.content

    def test_cards_page(self, test_client):
        """Test cards management page loads."""
        response = test_client.get("/cards")
        assert response.status_code == 200
        assert b"Manage Flashcards" in response.content

    def test_review_page(self, test_client, temp_db, sample_deck):
        """Test review page loads."""
        with patch('server.db', temp_db):
            response = test_client.get(f"/review/{sample_deck.id}")

        assert response.status_code == 200
        assert b"Reviewing:" in response.content

    def test_review_page_invalid_deck(self, test_client, temp_db):
        """Test review page with invalid deck ID."""
        with patch('server.db', temp_db):
            response = test_client.get("/review/99999")

        assert response.status_code == 404


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling."""

    def test_ai_service_unavailable(self, test_client):
        """Test handling when AI service is not configured."""
        with patch('server.get_ai_service', return_value=None):
            response = test_client.post("/api/generate-flashcards", json={
                "book_id": "test_book",
                "chapter_index": 0,
                "selected_text": "Test text",
                "num_cards": 1,
                "card_type": "basic"
            })

        assert response.status_code == 503
        assert "AI service not configured" in response.json()['detail']

    def test_nonexistent_card(self, test_client, temp_db):
        """Test operations on non-existent card."""
        with patch('server.db', temp_db):
            response = test_client.post(
                "/api/cards/99999/review",
                json={"rating": 3}
            )

        assert response.status_code == 404
