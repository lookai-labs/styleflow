from __future__ import annotations

from backend.app.rag.chatbot_rag.intents import (
    INTENT_GREETING,
    INTENT_IRRELEVANT,
    INTENT_MISSING_ANALYSIS,
    INTENT_NOISE,
    INTENT_SMALLTALK,
    INTENT_STYLE_EXPLANATION,
)
from backend.app.rag.chatbot_rag.static_responses import (
    GREETING_MESSAGE,
    IRRELEVANT_MESSAGE,
    MISSING_ANALYSIS_MESSAGE,
    MISSING_SELECTED_STYLE_MESSAGE,
    NOISE_MESSAGE,
    SMALLTALK_MESSAGE,
)

NON_LLM_INTENTS: set[str] = {
    INTENT_GREETING,
    INTENT_SMALLTALK,
    INTENT_IRRELEVANT,
    INTENT_NOISE,
    INTENT_MISSING_ANALYSIS,
}

NON_LLM_RESPONSES: dict[str, str] = {
    INTENT_GREETING: GREETING_MESSAGE,
    INTENT_SMALLTALK: SMALLTALK_MESSAGE,
    INTENT_IRRELEVANT: IRRELEVANT_MESSAGE,
    INTENT_NOISE: NOISE_MESSAGE,
    INTENT_MISSING_ANALYSIS: MISSING_ANALYSIS_MESSAGE,
    # selected_recommendation이 없을 때만 generate_non_rag_answer에서 사용됨
    INTENT_STYLE_EXPLANATION: MISSING_SELECTED_STYLE_MESSAGE,
}


def should_bypass_llm(intent: str | None) -> bool:
    return intent in NON_LLM_INTENTS


def get_bypass_response(intent: str | None) -> str | None:
    return NON_LLM_RESPONSES.get(intent)
