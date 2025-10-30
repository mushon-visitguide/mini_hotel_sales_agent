"""
Intent Classification for Smart Interruption Handling

Distinguishes between:
- status_check: User checking if agent is still working ("hi still there?")
- new_request: User wants something different ("actually make it 2 people")
- clarification: User adding details ("and we need parking")
- unknown: Ambiguous message

Uses hybrid approach:
1. Pattern matching for common cases (fast, <50ms)
2. LLM fallback for ambiguous cases (~200-500ms)
"""

import re
import logging
from enum import Enum
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)


class Intent(Enum):
    """Intent categories for message classification"""
    STATUS_CHECK = "status_check"
    NEW_REQUEST = "new_request"
    CLARIFICATION = "clarification"
    UNKNOWN = "unknown"


class IntentClassifier:
    """
    Fast intent classification for interruption handling.

    Uses pattern matching for common cases, LLM for ambiguous ones.

    Example:
        classifier = IntentClassifier(llm_client)

        # Fast pattern matching
        intent = await classifier.classify("hi still there?")
        # Returns Intent.STATUS_CHECK in <50ms

        # LLM fallback for ambiguous
        intent = await classifier.classify("can you add parking?")
        # Returns Intent.CLARIFICATION in ~200-500ms
    """

    # Pattern matching for instant classification
    STATUS_CHECK_PATTERNS = [
        r'^(hi|hello|hey|yo)[\s\?]*$',  # Just greetings
        r'(still|are you) (there|working|processing)',  # "still there?"
        r'^[\?]+$',  # Just question marks
        r'(hello|hi).*there',  # "hello are you there"
        r'taking (long|forever)',  # "taking too long?"
        r'(are you|you) (ok|alive|active)',  # "are you ok?"
        r'^ping[\?]*$',  # "ping?"
        r'(any|got) (update|news|progress)',  # "any update?"
    ]

    NEW_REQUEST_KEYWORDS = [
        'actually',
        'instead',
        'change',
        'cancel',
        'no wait',
        'make it',
        r'check\s+.*\s+instead',  # "check passover instead"
        'different',
        'another',
        'switch to',
        'never mind',
    ]

    CLARIFICATION_KEYWORDS = [
        r'^(and|also|plus)',  # Starts with "and" / "also"
        'make sure',
        'dont forget',
        r'(need|needs|want|wants)',  # "we need parking"
        'with',  # "with balcony"
        'has to have',
        'must have',
    ]

    def __init__(self, llm_client=None):
        """
        Initialize intent classifier.

        Args:
            llm_client: Optional LLM client for ambiguous cases
                       If None, always returns Intent.UNKNOWN for ambiguous cases
        """
        self.llm_client = llm_client

    async def classify(
        self,
        message: str,
        use_llm: bool = True,
        timeout_sec: float = 0.5
    ) -> Intent:
        """
        Classify message intent.

        Args:
            message: User's message
            use_llm: Fall back to LLM if pattern matching is uncertain
            timeout_sec: Max time for LLM classification (default 0.5s)

        Returns:
            Intent classification
        """
        message_lower = message.lower().strip()

        # Try pattern matching first (instant, <50ms)
        pattern_result = self._classify_by_patterns(message_lower)

        if pattern_result != Intent.UNKNOWN:
            logger.debug(f"Intent classified by patterns: {pattern_result.value} for '{message}'")
            return pattern_result

        # Fall back to LLM for ambiguous cases
        if use_llm and self.llm_client:
            try:
                llm_result = await asyncio.wait_for(
                    self._classify_by_llm(message),
                    timeout=timeout_sec
                )
                logger.debug(f"Intent classified by LLM: {llm_result.value} for '{message}'")
                return llm_result
            except asyncio.TimeoutError:
                logger.warning(f"LLM classification timed out for '{message}', defaulting to NEW_REQUEST")
                # Default to new request if LLM is slow (safer to cancel than to miss a new request)
                return Intent.NEW_REQUEST
            except Exception as e:
                logger.error(f"LLM classification failed: {e}, defaulting to NEW_REQUEST")
                return Intent.NEW_REQUEST

        # Default to new request if uncertain (safer to cancel than ignore)
        logger.debug(f"Intent unknown, defaulting to NEW_REQUEST for '{message}'")
        return Intent.NEW_REQUEST

    def _classify_by_patterns(self, message_lower: str) -> Intent:
        """
        Fast pattern-based classification.

        Args:
            message_lower: Lowercased message

        Returns:
            Intent if pattern matches, Intent.UNKNOWN otherwise
        """
        # Status checks (hi, hello, still there?)
        for pattern in self.STATUS_CHECK_PATTERNS:
            if re.search(pattern, message_lower):
                return Intent.STATUS_CHECK

        # New requests (actually, instead, change)
        for keyword in self.NEW_REQUEST_KEYWORDS:
            if re.search(keyword, message_lower):
                return Intent.NEW_REQUEST

        # Clarifications (and, also, make sure)
        for keyword in self.CLARIFICATION_KEYWORDS:
            if re.search(keyword, message_lower):
                return Intent.CLARIFICATION

        # Short messages with just question marks might be status checks
        if len(message_lower) <= 5 and '?' in message_lower:
            return Intent.STATUS_CHECK

        # Very short messages (< 10 chars) with no keywords are likely status checks
        if len(message_lower) < 10 and not any(c.isalpha() for c in message_lower):
            return Intent.STATUS_CHECK

        return Intent.UNKNOWN

    async def _classify_by_llm(self, message: str) -> Intent:
        """
        LLM-based classification for ambiguous cases.

        Args:
            message: User's message

        Returns:
            Intent classification
        """
        if not self.llm_client:
            return Intent.UNKNOWN

        prompt = f"""Classify this message into ONE category.

Message: "{message}"

Categories:
- status_check: User is checking if you're still working (e.g., "hi there?", "still processing?", "you ok?")
- new_request: User wants something different or is changing their request (e.g., "actually make it 2 people", "check Passover instead", "cancel that")
- clarification: User is adding details to current request (e.g., "and we need parking", "make sure it has wifi", "with balcony")

Reply with ONLY the category name (status_check, new_request, or clarification). No explanation.
"""

        try:
            response = await self.llm_client.quick_completion(
                prompt=prompt,
                max_tokens=20,
                temperature=0
            )

            response_lower = response.strip().lower()

            if "status_check" in response_lower:
                return Intent.STATUS_CHECK
            elif "new_request" in response_lower:
                return Intent.NEW_REQUEST
            elif "clarification" in response_lower:
                return Intent.CLARIFICATION

        except Exception as e:
            logger.error(f"LLM classification error: {e}")

        # Default to new request if unclear
        return Intent.NEW_REQUEST

    def is_status_check(self, message: str) -> bool:
        """
        Quick synchronous check if message is likely a status check.
        Only uses pattern matching (no LLM).

        Args:
            message: User's message

        Returns:
            True if likely status check
        """
        return self._classify_by_patterns(message.lower().strip()) == Intent.STATUS_CHECK

    def is_new_request(self, message: str) -> bool:
        """
        Quick synchronous check if message is likely a new request.
        Only uses pattern matching (no LLM).

        Args:
            message: User's message

        Returns:
            True if likely new request
        """
        return self._classify_by_patterns(message.lower().strip()) == Intent.NEW_REQUEST
