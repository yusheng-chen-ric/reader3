# Reader3: AI-Powered E-Reader with Flashcards & Q&A

A self-hosted EPUB reader with integrated AI features for creating flashcards and asking questions while you read. Transform your reading into an active learning experience with Anki-style spaced repetition and instant AI assistance.

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)

## Features

### 📚 E-Reader Core
- Clean, distraction-free EPUB reading interface
- Table of contents navigation
- Chapter-by-chapter reading with progress tracking
- Image support

### 🤖 AI-Powered Learning
- **Multi-Provider Support**: Works with Anthropic Claude, OpenAI GPT, Google Gemini, or local Ollama models
- **AI Q&A**: Ask questions about what you're reading and get instant answers with context awareness
- **Smart Flashcard Generation**: Select any text and generate flashcards automatically
- **Conversation History**: Maintains context across your Q&A sessions per chapter

### 🎴 Anki-Style Flashcards
- **SM-2 Spaced Repetition Algorithm**: The same proven algorithm used by Anki
- **Card Types**: Basic Q&A and Cloze deletion formats
- **Review Interface**: Four-button rating system (Again/Hard/Good/Easy)
- **Deck Management**: Organize cards by book automatically
- **Progress Tracking**: View new, learning, and due cards
- **Edit & Delete**: Full CRUD operations on your flashcards

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd reader3

# Install dependencies (using uv - fast Python package installer)
# Core dependencies
uv sync

# Optional: Install AI provider dependencies
# For Anthropic Claude:
uv sync --extra anthropic

# For OpenAI:
uv sync --extra openai

# For Google Gemini:
uv sync --extra gemini

# For all providers:
uv sync --extra all

# For local Ollama (no extra packages needed):
# Just install Ollama separately: https://ollama.ai
```

### 2. Configure AI Provider

Create a `config.json` file in the project root:

```json
{
  "ai": {
    "provider": "anthropic",
    "api_key": "your-api-key-here",
    "model": "claude-3-5-sonnet-20241022"
  }
}
```

**Provider Options:**

**Anthropic Claude:**
```json
{
  "ai": {
    "provider": "anthropic",
    "api_key": "sk-ant-...",
    "model": "claude-3-5-sonnet-20241022"
  }
}
```

**OpenAI:**
```json
{
  "ai": {
    "provider": "openai",
    "api_key": "sk-...",
    "model": "gpt-4o"
  }
}
```

**Google Gemini:**
```json
{
  "ai": {
    "provider": "gemini",
    "api_key": "AIza...",
    "model": "gemini-1.5-flash"
  }
}
```

**Ollama (Local):**
```json
{
  "ai": {
    "provider": "ollama",
    "model": "llama3.1",
    "base_url": "http://localhost:11434"
  }
}
```

### 3. Add Books

Process an EPUB file to make it readable:

```bash
uv run reader3.py your-book.epub
```

This creates a `your-book_data/` folder with processed content.

### 4. Start the Server

```bash
uv run server.py
```

Visit http://127.0.0.1:8123 to start reading!

## Usage Guide

### Reading Books

1. **Library View** (`/`): See all your processed books
2. **Reader View** (`/read/{book}/{chapter}`): Read with TOC navigation
3. **AI Sidebar**: Click "AI Tools" button to open/close the AI sidebar

### Creating Flashcards

1. **Select Text**: Highlight any passage while reading
2. **Open AI Sidebar**: Click "AI Tools" → "Flashcards" tab
3. **Choose Options**:
   - Card Type: Basic Q&A or Cloze Deletion
   - Number of Cards: 1-10
4. **Generate**: Click "Generate Flashcards"
5. Cards are automatically saved to the book's deck

### Asking Questions

1. **Open AI Sidebar**: Click "AI Tools" → "Q&A" tab
2. **Type Your Question**: Ask anything about the current chapter
3. **Get Instant Answers**: AI responds with context from your book
4. **Conversation History**: See your previous Q&As for this chapter

### Reviewing Flashcards

1. **View Decks** (`/decks`): See all your flashcard decks and statistics
2. **Study Now**: Click to start reviewing due cards
3. **Review Interface** (`/review/{deck_id}`):
   - See the question
   - Press Space (or click) to reveal the answer
   - Rate your recall:
     - **1 (Again)**: Forgot it - review again soon
     - **2 (Hard)**: Difficult - shorter interval
     - **3 (Good)**: Remembered correctly - normal interval
     - **4 (Easy)**: Too easy - longer interval

The SM-2 algorithm automatically schedules when you'll see each card next!

### Managing Cards

1. **Browse Cards** (`/cards`): View all flashcards
2. **Edit**: Modify front/back text
3. **Delete**: Remove unwanted cards
4. **Filter by Deck**: Select a specific deck to manage

## Project Structure

```
reader3/
├── server.py              # FastAPI web server & API endpoints
├── reader3.py             # EPUB processing engine
├── database.py            # SQLite database models
├── ai_providers.py        # Multi-provider AI abstraction
├── ai_service.py          # AI flashcard & Q&A generation
├── spaced_repetition.py   # SM-2 algorithm implementation
├── config.json            # AI configuration (create this)
├── config.example.json    # Example configuration
├── reader_data.db         # SQLite database (auto-created)
├── pyproject.toml         # Python dependencies
├── templates/             # HTML templates
│   ├── library.html       # Book library page
│   ├── reader.html        # Reading interface with AI sidebar
│   ├── decks.html         # Deck list page
│   ├── review.html        # Anki-style review interface
│   └── cards.html         # Card management page
└── *_data/                # Processed book folders
```

## API Endpoints

### AI Operations
- `POST /api/generate-flashcards` - Generate flashcards from text
- `POST /api/ask-question` - Ask a question about the book
- `GET /api/qa-history/{book_id}` - Get Q&A history

### Flashcard Management
- `GET /api/decks` - List all decks with stats
- `GET /api/decks/{deck_id}/cards` - Get cards in a deck
- `GET /api/cards/due` - Get cards due for review
- `POST /api/cards/{card_id}/review` - Submit a review rating
- `PUT /api/cards/{card_id}` - Update a card
- `DELETE /api/cards/{card_id}` - Delete a card

### Pages
- `GET /` - Library (list of books)
- `GET /read/{book_id}/{chapter}` - Reader interface
- `GET /decks` - Deck list
- `GET /review/{deck_id}` - Review interface
- `GET /cards` - Card management

## Technical Details

### Spaced Repetition (SM-2 Algorithm)

This is the same algorithm used by Anki:

- **New Cards**: Start with 1-day interval
- **Rating Effects**:
  - Again (1): Reset progress, review tomorrow
  - Hard (2): Increase interval by 1.2x, decrease ease
  - Good (3): Normal interval increase
  - Easy (4): Increase interval by 1.3x, increase ease
- **Ease Factor**: Adjusts based on your performance (1.3 - 2.5)
- **Interval Calculation**: `new_interval = old_interval × ease_factor`

### Database Schema

**Flashcards Table:**
- Content: front, back, card_type, tags, source_text
- SM-2 Fields: ease_factor, interval, repetitions, next_review
- Stats: total_reviews, lapses, created_at, updated_at

**Decks Table:**
- Organization: name, description, book_id

**Q&A History Table:**
- Tracking: book_id, chapter_index, question, answer, context

**Review Log Table:**
- Analytics: card_id, rating, time_taken, reviewed_at

## Environment Variables

You can use environment variables instead of `config.json`:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."
```

## Troubleshooting

### AI Service Not Available

```
Warning: AI service not available
Please configure your AI provider in config.json
```

**Solution**: Create `config.json` with your API key (see Configuration section)

### Import Errors

```
ImportError: anthropic package not installed
```

**Solution**: Install the provider package:
```bash
uv sync --extra anthropic  # or openai, gemini, all
```

### No Cards Generated

If flashcard generation returns empty or malformed cards:
- Check your AI API key is valid
- Ensure you selected enough text (20+ characters)
- Try a different AI model
- Check server logs for detailed errors

### Ollama Connection Failed

```
Error: Connection refused to localhost:11434
```

**Solution**:
1. Install Ollama: https://ollama.ai
2. Start Ollama: `ollama serve`
3. Pull a model: `ollama pull llama3.1`

## Development

### Adding a New AI Provider

1. Create a class inheriting from `AIProvider` in `ai_providers.py`
2. Implement `generate_completion()` and `generate_streaming()`
3. Add provider to `get_ai_provider()` factory function
4. Update `config.example.json` with example configuration

### Adding New Card Types

1. Update `AIService._generate_*_cards()` methods
2. Add UI option in `reader.html` flashcard tab
3. Update review interface if needed

## License

MIT

## Credits

- **SM-2 Algorithm**: Created by Piotr Woźniak for SuperMemo
- **Inspiration**: Anki flashcard app
- **EPUB Processing**: ebooklib library
- **Web Framework**: FastAPI

## Future Ideas

- [ ] Mobile-responsive design
- [ ] Dark mode
- [ ] PDF support
- [ ] Audio narration integration
- [ ] Statistics dashboard
- [ ] Export to Anki format
- [ ] Shared decks
- [ ] Multi-user support
- [ ] Reading goals & streaks

---

Happy reading and learning! 📚✨
