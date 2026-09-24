"""
Input Guardrails for MonArch AI.
Sanitizes user input, detects prompt injection attempts, redacts PII, and validates input safety.
"""

import re
from typing import Tuple


PROMPT_INJECTION_PATTERNS = [
    r"ignore (?:all|previous|above) (?:instructions|rules|prompts)",
    r"system prompt override",
    r"you are now (?:dan|jailbroken|unrestricted)",
    r"bypass safety guardrails",
    r"disregard context",
]

PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]"),
    (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[REDACTED_CREDIT_CARD]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "[REDACTED_EMAIL]"),
]


def sanitize_and_validate_input(user_input: str) -> Tuple[str, bool, str]:
    """
    Sanitizes user input, redacts PII, and tests against prompt injection patterns.
    Returns (sanitized_input, is_safe, reason).
    """
    if not user_input or not user_input.strip():
        return "", True, "Empty input"

    text = user_input.strip()

    # 1. Check for prompt injection
    text_lower = text.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return text, False, "Prompt injection attempt detected and blocked by MonArch Input Guardrail."

    # 2. Redact PII
    sanitized = text
    for pattern, replacement in PII_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized, True, "Input validated successfully."
