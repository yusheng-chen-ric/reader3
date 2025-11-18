import os
import pickle
from functools import lru_cache
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from reader3 import Book, BookMetadata, ChapterContent, TOCEntry
from database import Database, Flashcard, Deck, QAHistory, ReviewLog
from ai_service import AIService
from spaced_repetition import calculate_next_review, get_review_intervals, format_interval, is_card_due
from ai_providers import get_ai_provider

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize database
db = Database()

# Initialize AI service (will be lazy-loaded on first use)
ai_service = None

def get_ai_service():
    """Lazy-load AI service to avoid errors if config is missing."""
    global ai_service
    if ai_service is None:
        try:
            provider = get_ai_provider()
            ai_service = AIService(provider)
        except Exception as e:
            print(f"Warning: AI service not available: {e}")
            print("Please configure your AI provider in config.json")
    return ai_service

# Where are the book folders located?
BOOKS_DIR = "."

@lru_cache(maxsize=10)
def load_book_cached(folder_name: str) -> Optional[Book]:
    """
    Loads the book from the pickle file.
    Cached so we don't re-read the disk on every click.
    """
    file_path = os.path.join(BOOKS_DIR, folder_name, "book.pkl")
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "rb") as f:
            book = pickle.load(f)
        return book
    except Exception as e:
        print(f"Error loading book {folder_name}: {e}")
        return None


# ===== Pydantic Models for API =====

class GenerateFlashcardsRequest(BaseModel):
    book_id: str
    chapter_index: int
    selected_text: str
    context: Optional[str] = None
    num_cards: int = 3
    card_type: str = "basic"  # basic or cloze

class AskQuestionRequest(BaseModel):
    book_id: str
    chapter_index: int
    question: str
    context: str

class ReviewCardRequest(BaseModel):
    rating: int  # 1=Again, 2=Hard, 3=Good, 4=Easy

class UpdateCardRequest(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    tags: Optional[List[str]] = None


# ===== Original Routes =====

@app.get("/", response_class=HTMLResponse)
async def library_view(request: Request):
    """Lists all available processed books."""
    books = []

    # Scan directory for folders ending in '_data' that have a book.pkl
    if os.path.exists(BOOKS_DIR):
        for item in os.listdir(BOOKS_DIR):
            if item.endswith("_data") and os.path.isdir(item):
                # Try to load it to get the title
                book = load_book_cached(item)
                if book:
                    books.append({
                        "id": item,
                        "title": book.metadata.title,
                        "author": ", ".join(book.metadata.authors),
                        "chapters": len(book.spine)
                    })

    return templates.TemplateResponse("library.html", {"request": request, "books": books})

@app.get("/read/{book_id}", response_class=HTMLResponse)
async def redirect_to_first_chapter(book_id: str):
    """Helper to just go to chapter 0."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/read/{book_id}/0")

@app.get("/read/{book_id}/{chapter_index}", response_class=HTMLResponse)
async def read_chapter(request: Request, book_id: str, chapter_index: int):
    """The main reader interface with AI sidebar."""
    book = load_book_cached(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if chapter_index < 0 or chapter_index >= len(book.spine):
        raise HTTPException(status_code=404, detail="Chapter not found")

    current_chapter = book.spine[chapter_index]

    # Calculate Prev/Next links
    prev_idx = chapter_index - 1 if chapter_index > 0 else None
    next_idx = chapter_index + 1 if chapter_index < len(book.spine) - 1 else None

    # Get or create deck for this book
    deck_id = db.get_or_create_book_deck(book_id, book.metadata.title)

    # Get Q&A history for this chapter
    qa_history = db.get_qa_history(book_id, chapter_index, limit=10)

    return templates.TemplateResponse("reader.html", {
        "request": request,
        "book": book,
        "current_chapter": current_chapter,
        "chapter_index": chapter_index,
        "book_id": book_id,
        "prev_idx": prev_idx,
        "next_idx": next_idx,
        "deck_id": deck_id,
        "qa_history": qa_history
    })

@app.get("/read/{book_id}/images/{image_name}")
async def serve_image(book_id: str, image_name: str):
    """
    Serves images specifically for a book.
    The HTML contains <img src="images/pic.jpg">.
    The browser resolves this to /read/{book_id}/images/pic.jpg.
    """
    # Security check: ensure book_id is clean
    safe_book_id = os.path.basename(book_id)
    safe_image_name = os.path.basename(image_name)

    img_path = os.path.join(BOOKS_DIR, safe_book_id, "images", safe_image_name)

    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(img_path)


# ===== AI API Routes =====

@app.post("/api/generate-flashcards")
async def generate_flashcards(req: GenerateFlashcardsRequest):
    """Generate flashcards from selected text using AI."""
    service = get_ai_service()
    if not service:
        raise HTTPException(status_code=503, detail="AI service not configured")

    try:
        # Generate flashcards using AI
        cards_data = await service.generate_flashcards(
            text=req.selected_text,
            context=req.context,
            num_cards=req.num_cards,
            card_type=req.card_type
        )

        # Get or create deck for this book
        book = load_book_cached(req.book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        deck_id = db.get_or_create_book_deck(req.book_id, book.metadata.title)

        # Save flashcards to database
        created_cards = []
        for card_data in cards_data:
            card = Flashcard(
                deck_id=deck_id,
                book_id=req.book_id,
                chapter_index=req.chapter_index,
                front=card_data["front"],
                back=card_data["back"],
                card_type=req.card_type,
                source_text=req.selected_text[:500]  # Store first 500 chars
            )
            card_id = db.create_flashcard(card)
            card.id = card_id
            created_cards.append(card)

        return {
            "success": True,
            "cards": [
                {
                    "id": c.id,
                    "front": c.front,
                    "back": c.back,
                    "card_type": c.card_type
                }
                for c in created_cards
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating flashcards: {str(e)}")


@app.post("/api/ask-question")
async def ask_question(req: AskQuestionRequest):
    """Ask a question about the reading material."""
    service = get_ai_service()
    if not service:
        raise HTTPException(status_code=503, detail="AI service not configured")

    try:
        # Get book for title
        book = load_book_cached(req.book_id)
        book_title = book.metadata.title if book else None

        # Get conversation history
        qa_history = db.get_qa_history(req.book_id, req.chapter_index, limit=3)
        conversation_history = [
            {"question": qa.question, "answer": qa.answer}
            for qa in reversed(qa_history)
        ]

        # Generate answer
        answer = await service.answer_question(
            question=req.question,
            context=req.context,
            book_title=book_title,
            conversation_history=conversation_history
        )

        # Save to history
        qa = QAHistory(
            book_id=req.book_id,
            chapter_index=req.chapter_index,
            question=req.question,
            answer=answer,
            context=req.context[:1000]  # Store first 1000 chars
        )
        db.save_qa(qa)

        return {
            "success": True,
            "answer": answer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


# ===== Flashcard Management API Routes =====

@app.get("/api/decks")
async def get_decks():
    """Get all decks with statistics."""
    decks = db.get_all_decks()
    result = []

    for deck in decks:
        stats = db.get_deck_stats(deck.id)
        result.append({
            "id": deck.id,
            "name": deck.name,
            "description": deck.description,
            "book_id": deck.book_id,
            "stats": stats
        })

    return {"decks": result}


@app.get("/api/decks/{deck_id}/cards")
async def get_deck_cards(deck_id: int):
    """Get all cards in a deck."""
    cards = db.get_cards_by_deck(deck_id)

    return {
        "cards": [
            {
                "id": c.id,
                "front": c.front,
                "back": c.back,
                "card_type": c.card_type,
                "tags": c.tags,
                "ease_factor": c.ease_factor,
                "interval": c.interval,
                "repetitions": c.repetitions,
                "next_review": c.next_review.isoformat(),
                "total_reviews": c.total_reviews,
                "lapses": c.lapses,
                "is_due": is_card_due(c)
            }
            for c in cards
        ]
    }


@app.get("/api/cards/due")
async def get_due_cards(deck_id: Optional[int] = None, limit: int = 20):
    """Get cards due for review."""
    cards = db.get_cards_due_for_review(deck_id, limit)

    return {
        "cards": [
            {
                "id": c.id,
                "deck_id": c.deck_id,
                "front": c.front,
                "back": c.back,
                "card_type": c.card_type,
                "ease_factor": c.ease_factor,
                "interval": c.interval,
                "repetitions": c.repetitions
            }
            for c in cards
        ],
        "count": len(cards)
    }


@app.post("/api/cards/{card_id}/review")
async def review_card(card_id: int, req: ReviewCardRequest):
    """Submit a review for a card (Anki-style rating)."""
    if req.rating not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Rating must be 1-4")

    # Get the card
    card = db.get_flashcard(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Calculate intervals for preview
    intervals = get_review_intervals(card)

    # Update card with SM-2 algorithm
    updated_card = calculate_next_review(card, req.rating)
    db.update_flashcard(updated_card)

    # Log the review
    log = ReviewLog(card_id=card_id, rating=req.rating)
    db.log_review(log)

    return {
        "success": True,
        "card": {
            "id": updated_card.id,
            "ease_factor": updated_card.ease_factor,
            "interval": updated_card.interval,
            "repetitions": updated_card.repetitions,
            "next_review": updated_card.next_review.isoformat()
        },
        "next_intervals": {
            k: format_interval(v) for k, v in intervals.items()
        }
    }


@app.put("/api/cards/{card_id}")
async def update_card(card_id: int, req: UpdateCardRequest):
    """Update a flashcard."""
    card = db.get_flashcard(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if req.front is not None:
        card.front = req.front
    if req.back is not None:
        card.back = req.back
    if req.tags is not None:
        card.tags = req.tags

    db.update_flashcard(card)

    return {"success": True}


@app.delete("/api/cards/{card_id}")
async def delete_card(card_id: int):
    """Delete a flashcard."""
    db.delete_flashcard(card_id)
    return {"success": True}


@app.get("/api/qa-history/{book_id}")
async def get_qa_history_api(book_id: str, chapter_index: Optional[int] = None):
    """Get Q&A history for a book or chapter."""
    history = db.get_qa_history(book_id, chapter_index)

    return {
        "history": [
            {
                "id": qa.id,
                "question": qa.question,
                "answer": qa.answer,
                "chapter_index": qa.chapter_index,
                "created_at": qa.created_at.isoformat()
            }
            for qa in history
        ]
    }


# ===== UI Routes for Flashcard Management =====

@app.get("/decks", response_class=HTMLResponse)
async def decks_page(request: Request):
    """Page showing all decks."""
    decks = db.get_all_decks()
    decks_with_stats = []

    for deck in decks:
        stats = db.get_deck_stats(deck.id)
        decks_with_stats.append({
            "deck": deck,
            "stats": stats
        })

    return templates.TemplateResponse("decks.html", {
        "request": request,
        "decks": decks_with_stats
    })


@app.get("/review/{deck_id}", response_class=HTMLResponse)
async def review_page(request: Request, deck_id: int):
    """Page for reviewing flashcards with Anki-style interface."""
    deck = db.get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    stats = db.get_deck_stats(deck_id)

    return templates.TemplateResponse("review.html", {
        "request": request,
        "deck": deck,
        "stats": stats
    })


@app.get("/cards", response_class=HTMLResponse)
async def cards_management_page(request: Request):
    """Page for browsing and managing all flashcards."""
    decks = db.get_all_decks()

    return templates.TemplateResponse("cards.html", {
        "request": request,
        "decks": decks
    })


if __name__ == "__main__":
    import uvicorn
    print("Starting AI-powered e-reader server at http://127.0.0.1:8123")
    print("Make sure to configure your AI provider in config.json")
    uvicorn.run(app, host="127.0.0.1", port=8123)
