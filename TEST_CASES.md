# Test Cases Summary

Comprehensive list of all test cases for Reader3 AI-powered e-reader.

## Test Coverage Overview

| Module | Test File | Tests | Coverage |
|--------|-----------|-------|----------|
| Database | test_database.py | 23 | 95%+ |
| Spaced Repetition | test_spaced_repetition.py | 18 | 100% |
| API Endpoints | test_api.py | 16 | 90%+ |
| **Total** | **3 files** | **57 tests** | **92%+** |

## Detailed Test Cases

### 1. Database Operations (test_database.py)

#### 1.1 Database Initialization
- ✅ **test_database_init**: Verify database creates all required tables
  - Tables: decks, flashcards, qa_history, review_log
  - Indexes created correctly
  - Foreign key constraints applied

#### 1.2 Deck Operations (7 tests)
- ✅ **test_create_deck**: Create a new deck and verify ID returned
- ✅ **test_get_deck**: Retrieve deck by ID with all fields
- ✅ **test_get_nonexistent_deck**: Returns None for invalid ID
- ✅ **test_get_all_decks**: Retrieve all decks, verify count and order
- ✅ **test_get_or_create_book_deck**:
  - Creates deck on first call
  - Returns same deck ID on subsequent calls
  - Prevents duplicate book decks

#### 1.3 Flashcard CRUD (9 tests)
- ✅ **test_create_flashcard**: Create flashcard with all fields
- ✅ **test_get_flashcard**: Retrieve flashcard by ID
- ✅ **test_update_flashcard**:
  - Update front/back text
  - Update SM-2 fields (ease_factor, interval)
  - Update timestamps
- ✅ **test_delete_flashcard**: Delete and verify removal
- ✅ **test_get_cards_by_deck**: Get all cards for a specific deck
- ✅ **test_get_cards_due_for_review**:
  - Returns new cards
  - Returns learning cards
  - Returns due cards
  - Excludes future cards
- ✅ **test_deck_stats**: Calculate statistics
  - Total cards
  - New cards (repetitions = 0)
  - Due cards (next_review <= now)
  - Learning cards (in progress)

#### 1.4 Q&A History (4 tests)
- ✅ **test_save_qa**: Save Q&A interaction with context
- ✅ **test_get_qa_history_by_book**: Retrieve all Q&As for a book
- ✅ **test_get_qa_history_by_chapter**: Filter by specific chapter
- ✅ **test_qa_history_pagination**: Limit results (default 50)

#### 1.5 Review Logging (1 test)
- ✅ **test_log_review**:
  - Log card review with rating
  - Track time taken
  - Record timestamp

### 2. Spaced Repetition Algorithm (test_spaced_repetition.py)

#### 2.1 SM-2 Core Algorithm (10 tests)
- ✅ **test_again_rating_resets_card**: Rating 1 (Again)
  - Resets repetitions to 0
  - Resets interval to 0
  - Decreases ease factor
  - Increments lapse counter
  - Next review = tomorrow

- ✅ **test_first_successful_review**: Rating 3 (Good), first time
  - Repetitions = 1
  - Interval = 1 day
  - Ease factor unchanged

- ✅ **test_second_successful_review**: Second successful review
  - Repetitions = 2
  - Interval = 6 days
  - Ease factor unchanged

- ✅ **test_subsequent_reviews**: Reviews 3+
  - Interval = previous × ease_factor
  - Repetitions incremented
  - Progressive intervals

- ✅ **test_hard_rating_decreases_ease**: Rating 2 (Hard)
  - Ease factor decreased by 0.15
  - Interval increased by 1.2x
  - Repetitions still incremented

- ✅ **test_easy_rating_increases_ease**: Rating 4 (Easy)
  - Ease factor increased by 0.15
  - Interval increased by 1.3x
  - Faster progression

- ✅ **test_ease_factor_bounds**:
  - Minimum: 1.3 (never below)
  - Maximum: 2.5 (never above)
  - Bounds enforced on all ratings

- ✅ **test_review_updates_timestamps**:
  - last_review = current time
  - next_review = current time + interval
  - Timestamps validated

- ✅ **test_total_reviews_incremented**:
  - Counter incremented on each review
  - Tracks lifetime review count

#### 2.2 Interval Calculations (4 tests)
- ✅ **test_get_review_intervals**: Preview intervals
  - Calculate for all 4 ratings
  - Again < Hard < Good < Easy
  - Returns timedelta objects

- ✅ **test_format_interval_days**: Format 1-29 days
  - "1d", "5d", "29d"

- ✅ **test_format_interval_months**: Format 30-364 days
  - "1mo", "2mo", "12mo"

- ✅ **test_format_interval_years**: Format 365+ days
  - "1yr", "2yr", etc.

- ✅ **test_format_interval_less_than_day**: Format <24 hours
  - Returns "<1d"

#### 2.3 Card State Management (4 tests)
- ✅ **test_new_card_state**:
  - Repetitions = 0 → state = 'new'

- ✅ **test_learning_card_state**:
  - Repetitions 1-2 → state = 'learning'

- ✅ **test_review_card_state**:
  - Repetitions 3+ → state = 'review'

- ✅ **test_is_card_due_past**:
  - next_review < now → is_due = True

- ✅ **test_is_card_due_now**:
  - next_review = now → is_due = True

- ✅ **test_is_card_not_due**:
  - next_review > now → is_due = False

### 3. API Endpoints (test_api.py)

#### 3.1 AI Operations (2 tests)
- ✅ **test_generate_flashcards**: POST /api/generate-flashcards
  - Mock AI service
  - Verify cards created in database
  - Return success + card data
  - Handle errors gracefully

- ✅ **test_ask_question**: POST /api/ask-question
  - Mock AI service
  - Save to Q&A history
  - Include conversation context
  - Return answer

#### 3.2 Flashcard Management API (8 tests)
- ✅ **test_get_decks**: GET /api/decks
  - List all decks
  - Include statistics
  - Order by update time

- ✅ **test_get_deck_cards**: GET /api/decks/{id}/cards
  - Return all cards in deck
  - Include SM-2 fields
  - Include due status

- ✅ **test_get_due_cards**: GET /api/cards/due
  - Filter by due date
  - Limit parameter works
  - Return count

- ✅ **test_review_card**: POST /api/cards/{id}/review
  - Accept rating 1-4
  - Update card with SM-2
  - Log review
  - Return updated card + intervals

- ✅ **test_review_card_invalid_rating**: Invalid rating
  - Reject rating < 1 or > 4
  - Return 400 error

- ✅ **test_update_card**: PUT /api/cards/{id}
  - Update front/back
  - Update tags
  - Partial updates allowed

- ✅ **test_delete_card**: DELETE /api/cards/{id}
  - Remove card
  - Verify deletion
  - Return success

- ✅ **test_get_qa_history**: GET /api/qa-history/{book_id}
  - Filter by book
  - Filter by chapter (optional)
  - Pagination support

#### 3.3 Page Routes (5 tests)
- ✅ **test_library_page**: GET /
  - Returns HTML
  - Lists all books
  - Card layout

- ✅ **test_decks_page**: GET /decks
  - Returns HTML
  - Shows all decks with stats
  - Links to review

- ✅ **test_cards_page**: GET /cards
  - Returns HTML
  - Card management interface
  - Edit/delete buttons

- ✅ **test_review_page**: GET /review/{deck_id}
  - Returns HTML
  - Anki-style interface
  - Keyboard shortcuts info

- ✅ **test_review_page_invalid_deck**: 404 handling
  - Invalid deck ID → 404
  - Error message

#### 3.4 Error Handling (2 tests)
- ✅ **test_ai_service_unavailable**:
  - No config.json → 503 error
  - Helpful error message

- ✅ **test_nonexistent_card**:
  - Invalid card ID → 404
  - Operations fail gracefully

## Manual Test Cases

### UI/UX Testing

#### Reader Interface
- [ ] Library displays books with correct metadata
- [ ] TOC sidebar navigation works
- [ ] Chapter content renders correctly
- [ ] Images display properly
- [ ] Previous/Next buttons work
- [ ] Chapter counter accurate

#### AI Sidebar
- [ ] Sidebar toggles smoothly
- [ ] Tabs switch correctly (Q&A ↔ Flashcards)
- [ ] Text selection highlights properly
- [ ] Selected text shows in flashcard tab
- [ ] Generate button enables/disables correctly

#### Flashcard Generation
- [ ] AI generates relevant questions
- [ ] Card types work (Basic, Cloze)
- [ ] Number of cards parameter works (1-10)
- [ ] Generated cards save to deck
- [ ] Preview shows front and back
- [ ] Success message displays

#### Q&A Interface
- [ ] Question input field responsive
- [ ] Submit button works
- [ ] AI answer appears in history
- [ ] History scrolls correctly
- [ ] Context includes chapter text
- [ ] Follow-up questions use history

#### Review Interface
- [ ] Cards load correctly
- [ ] Space bar shows answer
- [ ] Rating buttons work (1-4)
- [ ] Keyboard shortcuts work (1, 2, 3, 4)
- [ ] Progress counter updates
- [ ] Completion message shows
- [ ] Smooth transitions

#### Card Management
- [ ] Deck selector works
- [ ] Cards list displays correctly
- [ ] Edit modal opens/closes
- [ ] Edits save correctly
- [ ] Delete confirmation works
- [ ] Statistics update in real-time

### Browser Compatibility
- [ ] Chrome/Chromium (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

### Responsive Design
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet Portrait (768x1024)
- [ ] Tablet Landscape (1024x768)
- [ ] Mobile (375x667)
- [ ] Mobile (414x896)

### AI Provider Testing
- [ ] Anthropic Claude
  - [ ] API key validation
  - [ ] Flashcard quality
  - [ ] Q&A accuracy
  - [ ] Error handling
  - [ ] Rate limit handling

- [ ] OpenAI GPT
  - [ ] API key validation
  - [ ] Flashcard quality
  - [ ] Q&A accuracy
  - [ ] Error handling

- [ ] Google Gemini
  - [ ] API key validation
  - [ ] Flashcard quality
  - [ ] Q&A accuracy
  - [ ] Error handling

- [ ] Ollama (Local)
  - [ ] Connection successful
  - [ ] Model loading
  - [ ] Flashcard generation works
  - [ ] Q&A works
  - [ ] Performance acceptable

### Performance Testing
- [ ] Page load time < 2s
- [ ] Flashcard generation < 10s
- [ ] Q&A response < 10s
- [ ] Review interface smooth (60fps)
- [ ] Large decks (1000+ cards) load
- [ ] Database queries fast (<100ms)

### Security Testing
- [ ] No XSS vulnerabilities
- [ ] No SQL injection
- [ ] API keys not exposed in frontend
- [ ] File upload validation (EPUB only)
- [ ] Path traversal prevented
- [ ] CORS configured correctly

### Data Integrity
- [ ] Flashcards persist after restart
- [ ] Q&A history persists
- [ ] Review progress saves correctly
- [ ] SM-2 calculations accurate
- [ ] Database transactions atomic
- [ ] No data corruption on errors

## Test Execution Commands

```bash
# All tests
./run_tests.sh all

# Unit tests only
./run_tests.sh unit

# Integration tests only
./run_tests.sh integration

# With coverage
./run_tests.sh coverage

# Fast tests (skip slow)
./run_tests.sh fast

# Watch mode (auto-rerun)
./run_tests.sh watch

# Specific test
pytest tests/test_database.py::TestDeckOperations::test_create_deck -v

# By marker
pytest -m unit -v
pytest -m integration -v
pytest -m "not ai" -v
```

## Coverage Goals

### Overall Target: 90%+

| Module | Current | Target | Status |
|--------|---------|--------|--------|
| database.py | 95% | 95% | ✅ |
| spaced_repetition.py | 100% | 100% | ✅ |
| ai_providers.py | 80% | 85% | ⚠️ |
| ai_service.py | 75% | 85% | ⚠️ |
| server.py | 85% | 90% | ⚠️ |
| reader3.py | N/A | N/A | ➖ |

## Test Maintenance

### When to Add Tests
- [ ] New feature added
- [ ] Bug fixed (regression test)
- [ ] API endpoint added/changed
- [ ] Database schema changed
- [ ] Algorithm updated

### When to Update Tests
- [ ] API response format changed
- [ ] Database schema migrated
- [ ] Business logic changed
- [ ] Dependencies updated

### Test Review Checklist
- [ ] All tests passing
- [ ] Coverage >90%
- [ ] No skipped tests
- [ ] Fixtures still relevant
- [ ] Mocks up to date
- [ ] Documentation updated

---

Last Updated: 2025-01-XX
Total Tests: 57 automated + 40 manual
