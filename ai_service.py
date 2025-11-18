"""
AI service for generating flashcards and answering questions.
"""

from typing import List, Dict, Any, Optional
from ai_providers import get_ai_provider, AIProvider
from database import Flashcard
import json
import re


class AIService:
    """Service for AI-powered flashcard generation and Q&A."""

    def __init__(self, provider: Optional[AIProvider] = None):
        """Initialize with an AI provider."""
        self.provider = provider or get_ai_provider()

    async def generate_flashcards(self, text: str, context: Optional[str] = None,
                                  num_cards: int = 3, card_type: str = "basic") -> List[Dict[str, str]]:
        """
        Generate flashcards from selected text.

        Args:
            text: The text to generate flashcards from
            context: Optional surrounding context for better understanding
            num_cards: Number of flashcards to generate
            card_type: Type of cards (basic, cloze)

        Returns:
            List of dicts with 'front' and 'back' keys
        """
        if card_type == "basic":
            return await self._generate_basic_cards(text, context, num_cards)
        elif card_type == "cloze":
            return await self._generate_cloze_cards(text, context, num_cards)
        else:
            raise ValueError(f"Unknown card type: {card_type}")

    async def _generate_basic_cards(self, text: str, context: Optional[str] = None,
                                    num_cards: int = 3) -> List[Dict[str, str]]:
        """Generate basic Q&A flashcards."""

        system_prompt = """You are an expert at creating educational flashcards.
Create clear, concise, and pedagogically effective flashcards that help with long-term retention.

Rules for good flashcards:
1. Each card should test ONE concept
2. Questions should be specific and unambiguous
3. Answers should be concise but complete
4. Use the exact terminology from the source text
5. Focus on key facts, definitions, relationships, and important details
6. Avoid yes/no questions
7. Make questions that require understanding, not just memorization"""

        context_text = f"\n\nSurrounding context:\n{context}" if context else ""

        prompt = f"""Generate {num_cards} high-quality flashcards from the following text.

Text:
{text}{context_text}

Return ONLY a JSON array of flashcards in this exact format:
[
  {{"front": "Question 1?", "back": "Answer 1"}},
  {{"front": "Question 2?", "back": "Answer 2"}},
  {{"front": "Question 3?", "back": "Answer 3"}}
]

Generate exactly {num_cards} flashcards. No additional text or explanation."""

        response = await self.provider.generate_completion(
            prompt=prompt,
            system=system_prompt,
            max_tokens=1500,
            temperature=0.7
        )

        # Extract JSON from response
        cards = self._extract_json(response)

        if not cards or not isinstance(cards, list):
            # Fallback: try to parse manually
            cards = self._parse_cards_fallback(response)

        return cards[:num_cards]

    async def _generate_cloze_cards(self, text: str, context: Optional[str] = None,
                                   num_cards: int = 3) -> List[Dict[str, str]]:
        """Generate cloze deletion flashcards."""

        system_prompt = """You are an expert at creating cloze deletion flashcards.
A cloze deletion card hides a key word or phrase that the learner must recall.

Format: Use [...] to indicate what should be hidden.
Example: "The capital of France is [Paris]" """

        context_text = f"\n\nSurrounding context:\n{context}" if context else ""

        prompt = f"""Generate {num_cards} cloze deletion flashcards from the following text.

Text:
{text}{context_text}

Return ONLY a JSON array of cloze flashcards in this exact format:
[
  {{"front": "The capital of France is [...]", "back": "Paris"}},
  {{"front": "DNA stands for [...]", "back": "Deoxyribonucleic acid"}}
]

Generate exactly {num_cards} flashcards. No additional text or explanation."""

        response = await self.provider.generate_completion(
            prompt=prompt,
            system=system_prompt,
            max_tokens=1500,
            temperature=0.7
        )

        cards = self._extract_json(response)

        if not cards or not isinstance(cards, list):
            cards = self._parse_cards_fallback(response)

        return cards[:num_cards]

    async def answer_question(self, question: str, context: str,
                             book_title: Optional[str] = None,
                             conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Answer a question about the reading material.

        Args:
            question: The user's question
            context: The current chapter text or relevant excerpt
            book_title: Optional book title for better context
            conversation_history: Optional previous Q&A for continuity

        Returns:
            AI-generated answer
        """

        system_prompt = """You are a knowledgeable reading assistant helping readers understand their books.

Your role:
1. Answer questions clearly and accurately based on the provided text
2. Explain concepts in an educational way
3. Make connections to other parts of the book when relevant
4. Admit when information isn't in the provided context
5. Be concise but thorough
6. Use examples from the text to support your answers"""

        book_context = f"Book: {book_title}\n\n" if book_title else ""

        # Build conversation context if available
        history_text = ""
        if conversation_history:
            history_text = "\n\nPrevious conversation:\n"
            for i, qa in enumerate(conversation_history[-3:]):  # Last 3 Q&As
                history_text += f"Q: {qa['question']}\nA: {qa['answer']}\n\n"

        prompt = f"""{book_context}Text excerpt:
{context[:3000]}

{history_text}
Current question: {question}

Please answer the question based on the provided text."""

        response = await self.provider.generate_completion(
            prompt=prompt,
            system=system_prompt,
            max_tokens=1000,
            temperature=0.7
        )

        return response.strip()

    async def generate_summary(self, text: str, summary_type: str = "brief") -> str:
        """
        Generate a summary of the text.

        Args:
            text: Text to summarize
            summary_type: 'brief', 'detailed', or 'key_points'

        Returns:
            Generated summary
        """

        if summary_type == "brief":
            system_prompt = "You create concise 2-3 sentence summaries of text passages."
            max_tokens = 200
        elif summary_type == "detailed":
            system_prompt = "You create comprehensive summaries that capture all important points."
            max_tokens = 500
        else:  # key_points
            system_prompt = "You extract key points from text as a bullet list."
            max_tokens = 400

        prompt = f"Summarize the following text:\n\n{text[:4000]}"

        response = await self.provider.generate_completion(
            prompt=prompt,
            system=system_prompt,
            max_tokens=max_tokens,
            temperature=0.5
        )

        return response.strip()

    def _extract_json(self, text: str) -> Optional[List[Dict[str, str]]]:
        """Extract JSON array from AI response."""
        try:
            # Try to find JSON array in the response
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Try parsing the whole response
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        return None

    def _parse_cards_fallback(self, text: str) -> List[Dict[str, str]]:
        """Fallback parser if JSON extraction fails."""
        cards = []

        # Try to find Q&A pairs in various formats
        # Format: "Q: ... A: ..."
        qa_pattern = r'(?:Q|Question|Front):\s*(.+?)\s*(?:A|Answer|Back):\s*(.+?)(?=(?:Q|Question|Front|$))'
        matches = re.finditer(qa_pattern, text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            front = match.group(1).strip()
            back = match.group(2).strip()
            # Clean up
            front = re.sub(r'^["\'\[\{]\s*|\s*["\'\]\}]$', '', front)
            back = re.sub(r'^["\'\[\{]\s*|\s*["\'\]\}]$', '', back)
            if front and back:
                cards.append({"front": front, "back": back})

        if not cards:
            # Last resort: try line by line
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            for i in range(0, len(lines) - 1, 2):
                if i + 1 < len(lines):
                    front = lines[i]
                    back = lines[i + 1]
                    # Remove numbering, bullets, etc.
                    front = re.sub(r'^\d+[\.\)]\s*', '', front)
                    back = re.sub(r'^\d+[\.\)]\s*', '', back)
                    if front and back:
                        cards.append({"front": front, "back": back})

        return cards
