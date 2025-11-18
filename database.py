"""
Database models and operations for flashcards, decks, and Q&A history.
Uses SQLite with Anki-style SM-2 spaced repetition algorithm.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class Flashcard:
    """Anki-style flashcard with SM-2 spaced repetition fields."""
    id: Optional[int] = None
    deck_id: int = None
    book_id: str = None  # e.g., "dracula"
    chapter_index: Optional[int] = None

    # Card content
    front: str = ""
    back: str = ""
    card_type: str = "basic"  # basic, cloze, reverse
    tags: List[str] = None
    source_text: Optional[str] = None  # Original text selection

    # SM-2 Algorithm fields
    ease_factor: float = 2.5  # Default ease factor
    interval: int = 0  # Days until next review (0 = new card)
    repetitions: int = 0  # Number of successful reviews
    next_review: datetime = None  # Next review date
    last_review: Optional[datetime] = None

    # Statistics
    total_reviews: int = 0
    lapses: int = 0  # Times the card was forgotten
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.next_review is None:
            self.next_review = datetime.now()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class Deck:
    """Collection of flashcards organized by topic/book."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    book_id: Optional[str] = None  # Link to a specific book, or None for custom decks
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class QAHistory:
    """Q&A interaction history while reading."""
    id: Optional[int] = None
    book_id: str = None
    chapter_index: Optional[int] = None
    question: str = ""
    answer: str = ""
    context: Optional[str] = None  # Chapter text or selection
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ReviewLog:
    """Log of card reviews for statistics and analytics."""
    id: Optional[int] = None
    card_id: int = None
    rating: int = 1  # 1=Again, 2=Hard, 3=Good, 4=Easy
    time_taken: Optional[int] = None  # Seconds taken to review
    reviewed_at: datetime = None

    def __post_init__(self):
        if self.reviewed_at is None:
            self.reviewed_at = datetime.now()


class Database:
    """Database manager for the e-reader flashcard system."""

    def __init__(self, db_path: str = "reader_data.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def init_db(self):
        """Initialize the database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Decks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                book_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Flashcards table with SM-2 fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL,
                book_id TEXT,
                chapter_index INTEGER,

                front TEXT NOT NULL,
                back TEXT NOT NULL,
                card_type TEXT DEFAULT 'basic',
                tags TEXT,
                source_text TEXT,

                ease_factor REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_review TIMESTAMP,

                total_reviews INTEGER DEFAULT 0,
                lapses INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
            )
        """)

        # Q&A History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id TEXT NOT NULL,
                chapter_index INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Review log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                time_taken INTEGER,
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (card_id) REFERENCES flashcards(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_deck ON flashcards(deck_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_book ON flashcards(book_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_next_review ON flashcards(next_review)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_book ON qa_history(book_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_card ON review_log(card_id)")

        conn.commit()
        conn.close()

    # ===== Deck Operations =====

    def create_deck(self, deck: Deck) -> int:
        """Create a new deck and return its ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO decks (name, description, book_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (deck.name, deck.description, deck.book_id, deck.created_at, deck.updated_at))

        deck_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return deck_id

    def get_deck(self, deck_id: int) -> Optional[Deck]:
        """Get a deck by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return Deck(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                book_id=row["book_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
        return None

    def get_all_decks(self) -> List[Deck]:
        """Get all decks."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM decks ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()

        return [Deck(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            book_id=row["book_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        ) for row in rows]

    def get_or_create_book_deck(self, book_id: str, book_title: str) -> int:
        """Get or create a deck for a specific book."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM decks WHERE book_id = ?", (book_id,))
        row = cursor.fetchone()

        if row:
            deck_id = row["id"]
        else:
            cursor.execute("""
                INSERT INTO decks (name, description, book_id)
                VALUES (?, ?, ?)
            """, (book_title, f"Flashcards from {book_title}", book_id))
            deck_id = cursor.lastrowid
            conn.commit()

        conn.close()
        return deck_id

    # ===== Flashcard Operations =====

    def create_flashcard(self, card: Flashcard) -> int:
        """Create a new flashcard and return its ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        tags_json = json.dumps(card.tags) if card.tags else "[]"

        cursor.execute("""
            INSERT INTO flashcards (
                deck_id, book_id, chapter_index, front, back, card_type, tags, source_text,
                ease_factor, interval, repetitions, next_review, last_review,
                total_reviews, lapses, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            card.deck_id, card.book_id, card.chapter_index, card.front, card.back,
            card.card_type, tags_json, card.source_text,
            card.ease_factor, card.interval, card.repetitions, card.next_review, card.last_review,
            card.total_reviews, card.lapses, card.created_at, card.updated_at
        ))

        card_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return card_id

    def get_flashcard(self, card_id: int) -> Optional[Flashcard]:
        """Get a flashcard by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_flashcard(row)
        return None

    def update_flashcard(self, card: Flashcard):
        """Update an existing flashcard."""
        conn = self.get_connection()
        cursor = conn.cursor()

        tags_json = json.dumps(card.tags) if card.tags else "[]"
        card.updated_at = datetime.now()

        cursor.execute("""
            UPDATE flashcards SET
                deck_id=?, book_id=?, chapter_index=?, front=?, back=?, card_type=?, tags=?, source_text=?,
                ease_factor=?, interval=?, repetitions=?, next_review=?, last_review=?,
                total_reviews=?, lapses=?, updated_at=?
            WHERE id=?
        """, (
            card.deck_id, card.book_id, card.chapter_index, card.front, card.back,
            card.card_type, tags_json, card.source_text,
            card.ease_factor, card.interval, card.repetitions, card.next_review, card.last_review,
            card.total_reviews, card.lapses, card.updated_at, card.id
        ))

        conn.commit()
        conn.close()

    def delete_flashcard(self, card_id: int):
        """Delete a flashcard."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM flashcards WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()

    def get_cards_by_deck(self, deck_id: int) -> List[Flashcard]:
        """Get all flashcards in a deck."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM flashcards WHERE deck_id = ? ORDER BY created_at DESC", (deck_id,))
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_flashcard(row) for row in rows]

    def get_cards_due_for_review(self, deck_id: Optional[int] = None, limit: int = 20) -> List[Flashcard]:
        """Get flashcards that are due for review."""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now()

        if deck_id:
            cursor.execute("""
                SELECT * FROM flashcards
                WHERE deck_id = ? AND next_review <= ?
                ORDER BY next_review ASC
                LIMIT ?
            """, (deck_id, now, limit))
        else:
            cursor.execute("""
                SELECT * FROM flashcards
                WHERE next_review <= ?
                ORDER BY next_review ASC
                LIMIT ?
            """, (now, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_flashcard(row) for row in rows]

    def get_deck_stats(self, deck_id: int) -> Dict[str, Any]:
        """Get statistics for a deck."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Total cards
        cursor.execute("SELECT COUNT(*) as count FROM flashcards WHERE deck_id = ?", (deck_id,))
        total = cursor.fetchone()["count"]

        # New cards (never reviewed)
        cursor.execute("SELECT COUNT(*) as count FROM flashcards WHERE deck_id = ? AND repetitions = 0", (deck_id,))
        new = cursor.fetchone()["count"]

        # Due cards
        now = datetime.now()
        cursor.execute("""
            SELECT COUNT(*) as count FROM flashcards
            WHERE deck_id = ? AND next_review <= ? AND repetitions > 0
        """, (deck_id, now))
        due = cursor.fetchone()["count"]

        conn.close()

        return {
            "total": total,
            "new": new,
            "due": due,
            "learning": total - new - due
        }

    # ===== Q&A History Operations =====

    def save_qa(self, qa: QAHistory) -> int:
        """Save a Q&A interaction."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO qa_history (book_id, chapter_index, question, answer, context, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (qa.book_id, qa.chapter_index, qa.question, qa.answer, qa.context, qa.created_at))

        qa_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return qa_id

    def get_qa_history(self, book_id: str, chapter_index: Optional[int] = None, limit: int = 50) -> List[QAHistory]:
        """Get Q&A history for a book or chapter."""
        conn = self.get_connection()
        cursor = conn.cursor()

        if chapter_index is not None:
            cursor.execute("""
                SELECT * FROM qa_history
                WHERE book_id = ? AND chapter_index = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (book_id, chapter_index, limit))
        else:
            cursor.execute("""
                SELECT * FROM qa_history
                WHERE book_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (book_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [QAHistory(
            id=row["id"],
            book_id=row["book_id"],
            chapter_index=row["chapter_index"],
            question=row["question"],
            answer=row["answer"],
            context=row["context"],
            created_at=datetime.fromisoformat(row["created_at"])
        ) for row in rows]

    # ===== Review Log Operations =====

    def log_review(self, log: ReviewLog) -> int:
        """Log a card review."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO review_log (card_id, rating, time_taken, reviewed_at)
            VALUES (?, ?, ?, ?)
        """, (log.card_id, log.rating, log.time_taken, log.reviewed_at))

        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return log_id

    # ===== Helper Methods =====

    def _row_to_flashcard(self, row) -> Flashcard:
        """Convert a database row to a Flashcard object."""
        tags = json.loads(row["tags"]) if row["tags"] else []

        return Flashcard(
            id=row["id"],
            deck_id=row["deck_id"],
            book_id=row["book_id"],
            chapter_index=row["chapter_index"],
            front=row["front"],
            back=row["back"],
            card_type=row["card_type"],
            tags=tags,
            source_text=row["source_text"],
            ease_factor=row["ease_factor"],
            interval=row["interval"],
            repetitions=row["repetitions"],
            next_review=datetime.fromisoformat(row["next_review"]) if row["next_review"] else None,
            last_review=datetime.fromisoformat(row["last_review"]) if row["last_review"] else None,
            total_reviews=row["total_reviews"],
            lapses=row["lapses"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
