# Testing Documentation

Comprehensive testing guide for Reader3 AI-powered e-reader application.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Test Cases](#test-cases)
- [Coverage Reports](#coverage-reports)
- [CI/CD Integration](#cicd-integration)
- [Writing New Tests](#writing-new-tests)

## Quick Start

### Install Test Dependencies

```bash
# Install development dependencies including pytest
uv sync --extra dev

# Optional: Install AI providers for AI tests
uv sync --extra all
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_database.py

# Run specific test class
pytest tests/test_database.py::TestDeckOperations

# Run specific test
pytest tests/test_database.py::TestDeckOperations::test_create_deck
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Fixtures and test configuration
├── test_database.py         # Database operations tests
├── test_spaced_repetition.py # SM-2 algorithm tests
└── test_api.py              # API endpoint tests
```

## Test Categories

Tests are organized using pytest markers:

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and classes in isolation
- Fast execution
- No external dependencies
- Examples: Database operations, SM-2 calculations

### Integration Tests (`@pytest.mark.integration`)
- Test multiple components working together
- API endpoint tests
- May involve database and mocked AI services

### AI Tests (`@pytest.mark.ai`)
- Tests requiring actual AI provider calls
- **WARNING**: These tests cost money (API calls)
- Skipped by default
- Only run when explicitly requested

### Slow Tests (`@pytest.mark.slow`)
- Tests that take longer to execute
- Can be skipped for quick test runs

## Running Tests

### Run Tests by Category

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run all except AI tests (default)
pytest -m "not ai"

# Run AI tests (costs money!)
pytest -m ai

# Run fast tests only
pytest -m "not slow"
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html

# Terminal coverage report
pytest --cov=. --cov-report=term-missing
```

### Watch Mode (auto-rerun on changes)

```bash
# Install pytest-watch
uv add --dev pytest-watch

# Run in watch mode
ptw
```

## Test Cases

### 1. Database Operations

#### Deck Management
- ✅ Create deck
- ✅ Get deck by ID
- ✅ Get all decks
- ✅ Get or create book-specific deck
- ✅ Deck statistics calculation

#### Flashcard CRUD
- ✅ Create flashcard
- ✅ Get flashcard by ID
- ✅ Update flashcard
- ✅ Delete flashcard
- ✅ Get cards by deck
- ✅ Get cards due for review
- ✅ Filter cards by state (new/learning/review)

#### Q&A History
- ✅ Save Q&A interaction
- ✅ Get Q&A history by book
- ✅ Get Q&A history by chapter
- ✅ History pagination

#### Review Logging
- ✅ Log card review
- ✅ Track review statistics
- ✅ Time tracking per review

### 2. Spaced Repetition (SM-2 Algorithm)

#### Core Algorithm
- ✅ Rating 1 (Again) - Resets card progress
- ✅ Rating 2 (Hard) - Decreases ease factor
- ✅ Rating 3 (Good) - Normal progression
- ✅ Rating 4 (Easy) - Increases ease factor
- ✅ First review (1 day interval)
- ✅ Second review (6 day interval)
- ✅ Subsequent reviews (ease factor multiplication)
- ✅ Ease factor bounds (1.3 - 2.5)
- ✅ Lapse counting

#### Interval Calculations
- ✅ Calculate intervals for all rating options
- ✅ Preview next review dates
- ✅ Format intervals (days, months, years)
- ✅ Handle edge cases (<1 day, >1 year)

#### Card States
- ✅ Identify new cards (0 repetitions)
- ✅ Identify learning cards (1-2 repetitions)
- ✅ Identify review cards (3+ repetitions)
- ✅ Determine if card is due

### 3. API Endpoints

#### AI Operations
- ✅ Generate flashcards from text
- ✅ Ask questions with context
- ✅ Handle AI service unavailable
- ✅ Validate input parameters
- ✅ Error handling for API failures

#### Flashcard Management API
- ✅ GET /api/decks - List all decks
- ✅ GET /api/decks/{id}/cards - Get deck cards
- ✅ GET /api/cards/due - Get due cards
- ✅ POST /api/cards/{id}/review - Submit review
- ✅ PUT /api/cards/{id} - Update card
- ✅ DELETE /api/cards/{id} - Delete card
- ✅ Invalid rating handling (must be 1-4)
- ✅ Non-existent card handling

#### Q&A API
- ✅ GET /api/qa-history/{book_id} - Get Q&A history
- ✅ Filter by chapter
- ✅ Pagination support

#### Page Routes
- ✅ GET / - Library page
- ✅ GET /read/{book_id}/{chapter} - Reader
- ✅ GET /decks - Decks list page
- ✅ GET /review/{deck_id} - Review page
- ✅ GET /cards - Card management page
- ✅ 404 handling for invalid IDs

### 4. Edge Cases & Error Handling

#### Data Validation
- ✅ Invalid rating values
- ✅ Non-existent resources (404)
- ✅ Missing required fields
- ✅ Database constraint violations

#### Service Availability
- ✅ AI service not configured
- ✅ Database connection errors
- ✅ Network failures (API calls)

#### Boundary Conditions
- ✅ Empty decks
- ✅ Zero cards due
- ✅ Very large intervals (years)
- ✅ Negative intervals (impossible)

## Test Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Database | 95%+ | ✅ |
| Spaced Repetition | 100% | ✅ |
| API Endpoints | 90%+ | ✅ |
| AI Service | 80%+ | ⚠️ Mocked |
| Templates | 70%+ | ⏳ Manual |

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to any branch
- Pull requests
- Scheduled daily runs

See `.github/workflows/test.yml` for configuration.

### Pre-commit Hooks (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Writing New Tests

### Test Structure Template

```python
import pytest

@pytest.mark.unit  # or integration, ai, slow
class TestMyFeature:
    """Test description."""

    def test_basic_functionality(self, fixture_name):
        """Test a specific behavior."""
        # Arrange
        input_data = "test"

        # Act
        result = my_function(input_data)

        # Assert
        assert result == expected_value

    def test_error_handling(self):
        """Test error cases."""
        with pytest.raises(ValueError):
            my_function(invalid_input)
```

### Using Fixtures

Common fixtures available in `conftest.py`:

- `temp_db` - Temporary database
- `sample_deck` - Pre-created deck
- `sample_flashcard` - Pre-created flashcard
- `sample_book` - Mock book object
- `test_client` - FastAPI test client
- `mock_ai_provider` - Mocked AI provider
- `multiple_flashcards` - Multiple cards in various states

### Best Practices

1. **Test one thing per test**
   - Each test should verify a single behavior
   - Use descriptive test names

2. **Use AAA pattern**
   - Arrange: Set up test data
   - Act: Execute the code under test
   - Assert: Verify the results

3. **Avoid test interdependence**
   - Tests should be able to run in any order
   - Use fixtures for setup, not other tests

4. **Mock external dependencies**
   - AI API calls
   - File system operations
   - Network requests

5. **Test both success and failure cases**
   - Happy path
   - Edge cases
   - Error conditions

## Manual Testing Checklist

Some features require manual testing:

### UI/UX Testing
- [ ] Library page displays books correctly
- [ ] Reader page loads and displays chapters
- [ ] AI sidebar opens/closes smoothly
- [ ] Text selection works for flashcard generation
- [ ] Q&A chat interface is responsive
- [ ] Flashcard review interface (keyboard shortcuts)
- [ ] Card editing modal works
- [ ] Statistics display correctly

### Browser Compatibility
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

### Responsive Design
- [ ] Desktop (1920x1080)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

### AI Provider Testing
- [ ] Anthropic Claude generates good flashcards
- [ ] OpenAI GPT generates good flashcards
- [ ] Google Gemini generates good flashcards
- [ ] Ollama (local) works correctly
- [ ] Error messages are helpful

## Troubleshooting Tests

### Tests Failing Locally

```bash
# Clear pytest cache
pytest --cache-clear

# Run with more verbose output
pytest -vv

# Run with print statements visible
pytest -s

# Run single test for debugging
pytest tests/test_database.py::test_create_deck -vv -s
```

### Database Tests Failing

```bash
# Check if temp files are being cleaned up
ls /tmp/*.db

# Run with fresh database
rm -f reader_data.db test*.db
pytest
```

### Import Errors

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
uv sync --extra dev --extra all
```

## Performance Testing

### Load Testing (Future)

```bash
# Install locust
uv add --dev locust

# Run load tests
locust -f tests/load_test.py
```

### Benchmarking (Future)

```bash
# Install pytest-benchmark
uv add --dev pytest-benchmark

# Run benchmarks
pytest tests/test_performance.py --benchmark-only
```

## Testing Checklist for New Features

When adding a new feature:

- [ ] Write unit tests for core logic
- [ ] Write integration tests for API endpoints
- [ ] Update fixtures if needed
- [ ] Add test cases to this document
- [ ] Achieve >90% coverage for new code
- [ ] Test error handling
- [ ] Test edge cases
- [ ] Update CI/CD if needed
- [ ] Add manual testing steps if applicable

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

Last Updated: 2025-01-XX
