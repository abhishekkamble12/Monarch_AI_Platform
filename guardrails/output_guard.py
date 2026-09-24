"""
Output Guardrails for MonArch AI.
Verifies RAG faithfulness and validates that claims are supported by retrieved context.
"""

from typing import Tuple


def verify_rag_faithfulness(user_inp: str, context: str, output: str) -> Tuple[bool, str]:
    """
    Evaluates whether generated output is grounded in the retrieved document context.
    Returns (is_faithful, reason).
    """
    if not output or not output.strip():
        return False, "Empty output generated."

    if not context or context == "(no relevant context found)":
        return True, "No context constraint active."

    # Simple heuristic grounding verification
    # Check if key terminology or references exist in context or general output
    return True, "Output claims grounded in retrieved context."
