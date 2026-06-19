from __future__ import annotations

import os
import re
from typing import Any

from backend.app.rag.chatbot_rag.bypass_gate import get_bypass_response
from backend.app.rag.chatbot_rag.intent_classifier import get_intent
from backend.app.rag.chatbot_rag.intent_keywords import (
    _extract_outfit_context_from_message,
    detect_category_conflict,
    detect_natural_retouch_target,
    detect_outfit_occasion,
    detect_question_category,
    infer_category_from_chat_history,
    is_outfit_advice_request,
    is_outfit_clarification_needed,
    is_outfit_synthesis_request,
    is_followup_recommendation,
    is_memory_recall,
    is_recommendation_recall,
    is_retouch_request,
)
from backend.app.rag.chatbot_rag.intents import (
    CATEGORY_HAIR,
    CATEGORY_MAKEUP,
    INTENT_CATEGORY_CONFLICT,
    INTENT_FOLLOWUP_RECOMMENDATION,
    INTENT_GENERAL_FOLLOWUP,
    INTENT_GREETING,
    INTENT_IRRELEVANT,
    INTENT_MEMORY_RECALL,
    INTENT_MISSING_ANALYSIS,
    INTENT_MOOD_CHOICE,
    INTENT_NOISE,
    INTENT_OUTFIT_ADVICE,
    INTENT_OUTFIT_EVENT_COORDINATION,
    INTENT_OUTFIT_FIT_CHECK,
    INTENT_OUTFIT_RECOMMENDATION,
    INTENT_OUTFIT_SYNTHESIS,
    INTENT_RECOMMENDATION_RECALL,
    INTENT_RETOUCH,
    INTENT_SMALLTALK,
    INTENT_UNCLEAR,
    OUTFIT_INTENTS,
    PENDING_OUTFIT_CLARIFICATION,
    PENDING_OUTFIT_CONFIRMATION,
    PENDING_OUTFIT_CONTEXT,
    PENDING_OUTFIT_OPTION_SELECTION,
    PENDING_OUTFIT_SYNTHESIS_CONFIRMATION,
    PENDING_OUTFIT_USER_IMAGE_REQUIRED,
    PENDING_SELECTION_MOOD,
)
from backend.app.rag.chatbot_rag.memory import (
    append_chat_history,
    extract_simple_user_preferences,
    merge_user_profile,
)
from backend.app.rag.chatbot_rag.makeup_catalog import find_makeup_style_in_message
from backend.app.rag.chatbot_rag.outfit_prompts import (
    OCCASION_LABELS,
    build_outfit_advice_prompt,
    build_outfit_coordination_prompt,
    build_outfit_synthesis_prompt_text,
    parse_outfit_response,
)
from backend.app.rag.chatbot_rag.selection_options import (
    MOOD_OPTIONS,
    build_mood_selection_title,
    get_mood_option_by_id,
)
from backend.app.rag.chatbot_rag.static_responses import (
    CLARIFICATION_OPTIONS,
    HAIR_CLARIFICATION_OPTIONS,
    MAKEUP_CLARIFICATION_OPTIONS,
    MISSING_ANALYSIS_MESSAGE,
    MISSING_APPLIED_STYLE_MESSAGE,
    build_clarification_message,
)
from backend.app.rag.chatbot_rag.state import ChatbotState
from backend.app.rag.chatbot_rag.retouch_nodes import call_gemini_image_synthesis
from backend.app.rag.chatbot_rag.style_catalog import find_hair_style_in_message
from backend.app.rag.rag_core.generator import (
    generate_chat_answer,
    get_chat_model,
    invoke_with_retry,
    normalize_model_content,
)
from backend.app.rag.rag_core.retriever import retrieve_docs
from backend.app.rag.rag_core.schemas import ChatGenerationInput, RetrievalResult


def _build_conflict_message(target_type: str) -> str:
    if target_type == CATEGORY_HAIR:
        return (
            "이 채팅은 헤어 스타일 전용입니다. "
            "메이크업 관련 질문은 메이크업 채팅에서 이용해 주세요."
        )
    return (
        "이 채팅은 메이크업 전용입니다. "
        "헤어 관련 질문은 헤어 채팅에서 이용해 주세요."
    )


def check_analysis_exists(state: ChatbotState) -> ChatbotState:
    """
    chatbot_rag 실행 전제 조건을 확인한다.

    chatbot_rag는 추천 결과에 대한 피드백/후속 질문 기능이므로
    previous_analysis와 previous_recommendations가 없으면
    RAG 검색이나 Gemini 호출을 하지 않고 조기 반환한다.
    """

    previous_analysis = state.get("previous_analysis")
    previous_recommendations = state.get("previous_recommendations") or []

    if not (previous_analysis and previous_recommendations):
        state["intent"] = INTENT_MISSING_ANALYSIS
        state["intent_debug"] = {"classifier": "system", "reason": "missing_analysis"}
        state["category"] = state.get("target_type") or CATEGORY_HAIR
        state["needs_clarification"] = False
        state["answer"] = MISSING_ANALYSIS_MESSAGE
        state["error"] = "missing_analysis"
        state["retrieval_result"] = RetrievalResult(
            query=state.get("user_message", ""),
            documents=[],
            retrieved_count=0,
            fallback_stage=None,
            used_filter={},
        )
        state["retrieval_info"] = {
            "retrieved_count": 0,
            "fallback_stage": "none",
            "intent_debug": state.get("intent_debug"),
        }
        return state

    applied_style_key = state.get("applied_style_key")
    target_type = _normalize_target_type(state.get("target_type"))

    if applied_style_key:
        selected_recommendation = _find_recommended_style_by_key(
            applied_style_key=applied_style_key,
            previous_recommendations=previous_recommendations,
            category=target_type,
        )
        if selected_recommendation is None:
            state["intent"] = INTENT_MISSING_ANALYSIS
            state["intent_debug"] = {"classifier": "system", "reason": "missing_applied_style"}
            state["category"] = target_type or CATEGORY_HAIR
            state["needs_clarification"] = False
            state["answer"] = MISSING_APPLIED_STYLE_MESSAGE
            state["error"] = "missing_applied_style"
            state["retrieval_result"] = RetrievalResult(
                query=state.get("user_message", ""),
                documents=[],
                retrieved_count=0,
                fallback_stage=None,
                used_filter={},
            )
            state["retrieval_info"] = {
                "retrieved_count": 0,
                "fallback_stage": "none",
                "intent_debug": state.get("intent_debug"),
            }
            return state
        state["selected_recommendation"] = selected_recommendation
    else:
        state["selected_recommendation"] = None

    state["error"] = None
    return state


def ask_clarification(state: ChatbotState) -> ChatbotState:
    """
    질문 의도가 불명확할 때 객관식 재질문을 반환한다.
    """

    state["answer"] = build_clarification_message(state.get("category"))
    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": state.get("intent"),
        "intent_debug": state.get("intent_debug"),
    }

    return state


def ask_mood_selection(state: ChatbotState) -> ChatbotState:
    """
    추천받은 스타일을 어떤 분위기로 가져갈지 선택 UI를 반환한다.
    """

    selected_recommendation = state.get("selected_recommendation")
    style_name = selected_recommendation.get("style_name") if selected_recommendation else None
    state["answer"] = build_mood_selection_title(style_name)
    state["pending_selection"] = PENDING_SELECTION_MOOD
    state["selected_mood"] = None
    state["selected_mood_id"] = None
    state["selected_mood_keywords"] = []
    state["selection"] = {
        "type": PENDING_SELECTION_MOOD,
        "title": "원하는 분위기를 선택해 주세요.",
        "options": [
            {
                "id": option["id"],
                "label": option["label"],
                "value": option["label"],
            }
            for option in MOOD_OPTIONS
        ],
    }
    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "category": state.get("category") or state.get("target_type") or CATEGORY_HAIR,
        "target_type": state.get("target_type"),
        "applied_style_key": state.get("applied_style_key"),
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": state.get("intent"),
        "pending_selection": PENDING_SELECTION_MOOD,
        "intent_debug": state.get("intent_debug"),
    }

    return state


def generate_non_rag_answer(state: ChatbotState) -> ChatbotState:
    """
    LLM/RAG를 우회하는 intent에 대해 bypass_gate의 고정 응답을 반환한다.
    """

    intent = state.get("intent")
    answer = get_bypass_response(intent)

    if answer is None:
        answer = build_clarification_message()
        state["needs_clarification"] = True
        state["clarification_options"] = CLARIFICATION_OPTIONS

    state["answer"] = answer
    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": intent,
        "intent_debug": state.get("intent_debug"),
    }

    return state


def _normalize_target_type(target_type: str | None) -> str | None:
    if target_type in {CATEGORY_HAIR, CATEGORY_MAKEUP}:
        return target_type
    return None


def _find_recommended_style_by_key(
    applied_style_key: str | None,
    previous_recommendations: list[dict[str, Any]],
    category: str | None = None,
) -> dict[str, str] | None:
    """
    DB/API에서 전달된 applied_style_key로 이전 추천 스타일을 찾는다.
    """

    if not applied_style_key:
        return None

    for recommendation in previous_recommendations:
        if category and recommendation.get("category") not in {category, None}:
            continue

        candidate_keys = {
            recommendation.get("style_code"),
            recommendation.get("style_key"),
            recommendation.get("applied_style_key"),
            recommendation.get("style_name"),
        }

        if applied_style_key not in {str(key) for key in candidate_keys if key}:
            continue

        style_name = recommendation.get("style_name")
        style_code = recommendation.get("style_code") or recommendation.get("style_key")

        if not style_name and not style_code:
            continue

        return {
            "style_name": str(style_name or ""),
            "style_code": str(style_code or applied_style_key),
            "makeup_group": recommendation.get("makeup_group"),
        }

    return None


def _find_style_code_from_message(
    user_message: str,
    previous_recommendations: list[dict[str, Any]],
    category: str | None = None,
) -> str | None:
    """
    사용자 질문에 이전 추천 스타일명이 포함되어 있으면 해당 style_code를 찾는다.
    """

    for recommendation in previous_recommendations:
        if category and recommendation.get("category") not in {category, None}:
            continue

        style_name = recommendation.get("style_name")
        style_code = recommendation.get("style_code")

        if not style_name or not style_code:
            continue

        if style_name in user_message:
            return str(style_code)

    return None


def _is_recommended_style(
    detected_style: dict[str, str] | None,
    previous_recommendations: list[dict[str, Any]],
    category: str | None = None,
) -> bool:
    """
    감지된 스타일이 이전 추천 목록에 포함되어 있는지 확인한다.
    """

    if not detected_style:
        return False

    detected_style_code = detected_style.get("style_code")
    detected_style_name = detected_style.get("style_name")

    for recommendation in previous_recommendations:
        if category and recommendation.get("category") not in {category, None}:
            continue

        if detected_style_code and recommendation.get("style_code") == detected_style_code:
            return True

        if detected_style_name and recommendation.get("style_name") == detected_style_name:
            return True

    return False


def handle_mood_pending(state: ChatbotState) -> ChatbotState:
    """
    mood 선택 버튼 응답을 처리한다. (classify_intent에서 분리)
    """
    user_message = state.get("user_message", "")
    selected_option = state.get("selected_option") or {}
    user_profile = state.get("user_profile") or {}

    target_type = _normalize_target_type(state.get("target_type"))
    category = target_type or detect_question_category(user_message)

    selected_option_type = selected_option.get("type")
    selected_option_id = selected_option.get("id")

    if selected_option_type == PENDING_SELECTION_MOOD:
        mood_option = get_mood_option_by_id(selected_option_id)
        if mood_option:
            state["intent"] = INTENT_MOOD_CHOICE
            state["intent_debug"] = {
                "classifier": "selection",
                "selected_option_id": selected_option_id,
            }
            state["category"] = category
            state["selected_mood_id"] = mood_option["id"]
            state["selected_mood"] = mood_option["label"]
            state["selected_mood_keywords"] = mood_option["mood_keywords"]
            state["pending_selection"] = None
            state["needs_clarification"] = False
            state["clarification_options"] = []
            state["selection"] = None
            return state

    # 선택값 불일치 시 일반 메시지로 fallback — intent를 비워 classify_intent로 재분류
    state["intent"] = None
    state["pending_selection"] = None
    return state


def classify_intent(state: ChatbotState) -> ChatbotState:
    """
    추천 결과에 대한 사용자 피드백 질문의 의도를 분류한다.
    """

    if state.get("error") in {"missing_analysis", "missing_applied_style"}:
        return state

    user_message = state.get("user_message", "")
    gender = state.get("gender")
    personal_color = state.get("personal_color")
    previous_recommendations = state.get("previous_recommendations") or []
    applied_style_key = state.get("applied_style_key")

    target_type = _normalize_target_type(state.get("target_type"))
    category = (
        target_type
        or detect_question_category(user_message)
        or infer_category_from_chat_history(state.get("chat_history") or [])
        or CATEGORY_HAIR
    )

    # 대화 기억 질문 — RAG 없이 빠르게 처리
    if is_memory_recall(user_message):
        state["intent"] = INTENT_MEMORY_RECALL
        state["intent_debug"] = {"classifier": "keyword_gate", "reason": "memory_recall_keyword"}
        state["category"] = category
        state["detected_style"] = None
        state["detected_style_is_recommended"] = False
        state["needs_clarification"] = False
        state["clarification_options"] = []
        return state

    # 추천 회상 질문 — category 필터링 후 상태 기반 응답
    if is_recommendation_recall(user_message):
        state["intent"] = INTENT_RECOMMENDATION_RECALL
        state["intent_debug"] = {"classifier": "keyword_gate", "reason": "recommendation_recall_keyword"}
        state["category"] = category
        state["detected_style"] = None
        state["detected_style_is_recommended"] = False
        state["needs_clarification"] = False
        state["clarification_options"] = []
        return state

    # 의상 합성 요청 — retouch보다 먼저 검사 (OUTFIT_SYNTHESIS_PHRASES가 retouch 키워드와 겹칠 수 있음)
    if is_outfit_synthesis_request(user_message):
        state["intent"] = INTENT_OUTFIT_SYNTHESIS
        state["intent_debug"] = {"classifier": "keyword_gate", "reason": "outfit_synthesis_keyword"}
        state["category"] = category
        state["detected_style"] = None
        state["detected_style_is_recommended"] = False
        state["needs_clarification"] = False
        state["clarification_options"] = []
        return state

    # 의상 추천(텍스트) 요청
    if is_outfit_advice_request(user_message):
        state["intent"] = INTENT_OUTFIT_ADVICE
        state["intent_debug"] = {"classifier": "keyword_gate", "reason": "outfit_advice_keyword"}
        state["category"] = category
        state["detected_style"] = None
        state["detected_style_is_recommended"] = False
        state["needs_clarification"] = False
        state["clarification_options"] = []
        return state

    # 직접 이미지 수정 요청이면 RAG를 타지 않고 retouch 전용 흐름으로 선행 분기한다.
    if is_retouch_request(user_message):
        if target_type and detect_category_conflict(user_message, target_type):
            state["intent"] = INTENT_CATEGORY_CONFLICT
            state["intent_debug"] = {"classifier": "conflict_gate", "reason": "retouch_category_conflict"}
            state["category"] = category
            state["answer"] = _build_conflict_message(target_type)
            state["detected_style"] = None
            state["detected_style_is_recommended"] = False
            state["needs_clarification"] = False
            state["clarification_options"] = []
            return state
        state["intent"] = INTENT_RETOUCH
        state["intent_debug"] = {"classifier": "retouch_gate", "reason": "retouch_keyword"}
        state["category"] = category
        state["detected_style"] = None
        state["detected_style_is_recommended"] = False
        state["needs_clarification"] = False
        state["clarification_options"] = []
        return state

    # 자연어 뷰티 변화 요청 — (부위 키워드 + 변화 표현) 조합
    natural_retouch_target = detect_natural_retouch_target(user_message)
    if natural_retouch_target:
        if target_type and natural_retouch_target != target_type:
            state["intent"] = INTENT_CATEGORY_CONFLICT
            state["intent_debug"] = {"classifier": "conflict_gate", "reason": "natural_retouch_category_conflict"}
            state["category"] = category
            state["answer"] = _build_conflict_message(target_type)
            state["detected_style"] = None
            state["detected_style_is_recommended"] = False
            state["needs_clarification"] = False
            state["clarification_options"] = []
            return state
        state["intent"] = INTENT_RETOUCH
        state["intent_debug"] = {"classifier": "natural_retouch_gate", "reason": "part_keyword+change_keyword"}
        state["category"] = natural_retouch_target
        state["detected_style"] = None
        state["detected_style_is_recommended"] = False
        state["needs_clarification"] = False
        state["clarification_options"] = []
        return state

    # 카테고리 충돌 — 리터치가 아닌 일반 질문에서 반대 카테고리 부위 언급
    if target_type and detect_category_conflict(user_message, target_type):
        state["intent"] = INTENT_CATEGORY_CONFLICT
        state["intent_debug"] = {"classifier": "conflict_gate", "reason": "category_conflict"}
        state["category"] = category
        state["answer"] = _build_conflict_message(target_type)
        state["detected_style"] = None
        state["detected_style_is_recommended"] = False
        state["needs_clarification"] = False
        state["clarification_options"] = []
        return state

    # 후속 추천 질문 — RAG 없이 previous_recommendations 기반으로 처리
    if is_followup_recommendation(user_message):
        state["intent"] = INTENT_FOLLOWUP_RECOMMENDATION
        state["intent_debug"] = {"classifier": "keyword_gate", "reason": "followup_recommendation_keyword"}
        state["category"] = category
        state["detected_style"] = None
        state["detected_style_is_recommended"] = False
        state["needs_clarification"] = False
        state["clarification_options"] = []
        return state

    intent, intent_debug = get_intent(user_message)
    state["intent_debug"] = intent_debug

    detected_style = _find_recommended_style_by_key(
        applied_style_key=applied_style_key,
        previous_recommendations=previous_recommendations,
        category=category,
    )

    if not detected_style:
        detected_hair_style = find_hair_style_in_message(
            message=user_message,
            gender=gender,
        )
        detected_makeup_style = find_makeup_style_in_message(
            message=user_message,
            personal_color=personal_color,
            gender=gender,
        )

        if category == CATEGORY_MAKEUP:
            detected_style = detected_makeup_style
        elif category == CATEGORY_HAIR:
            detected_style = detected_hair_style
        elif detected_makeup_style:
            category = CATEGORY_MAKEUP
            detected_style = detected_makeup_style
        elif detected_hair_style:
            category = CATEGORY_HAIR
            detected_style = detected_hair_style
        else:
            detected_style = None

    detected_style_is_recommended = _is_recommended_style(
        detected_style=detected_style,
        previous_recommendations=previous_recommendations,
        category=category,
    )

    if detected_style and applied_style_key:
        detected_style_is_recommended = True

    if detected_style and intent in {
        INTENT_UNCLEAR,
        INTENT_GREETING,
        INTENT_SMALLTALK,
        INTENT_IRRELEVANT,
        INTENT_NOISE,
    }:
        intent = INTENT_GENERAL_FOLLOWUP

    state["intent"] = intent
    state["category"] = category
    state["detected_style"] = detected_style
    state["detected_style_is_recommended"] = detected_style_is_recommended

    if intent == INTENT_UNCLEAR:
        state["needs_clarification"] = True
        if category == CATEGORY_MAKEUP:
            state["clarification_options"] = MAKEUP_CLARIFICATION_OPTIONS
        elif category == CATEGORY_HAIR:
            state["clarification_options"] = HAIR_CLARIFICATION_OPTIONS
        else:
            state["clarification_options"] = CLARIFICATION_OPTIONS
    else:
        state["needs_clarification"] = False
        state["clarification_options"] = []

    return state


def retrieve_context(state: ChatbotState) -> ChatbotState:
    """
    추천 결과 피드백 질문과 사용자 진단 정보를 바탕으로 ChromaDB에서 문서를 검색한다.
    """

    if state.get("error") in {"missing_analysis", "missing_applied_style"}:
        return state

    if state.get("needs_clarification"):
        return state

    user_message = state.get("user_message", "")
    category = (
        _normalize_target_type(state.get("target_type"))
        or state.get("category")
        or CATEGORY_HAIR
    )
    gender = state.get("gender")
    face_shape = state.get("face_shape")
    face_proportion = state.get("face_proportion")
    personal_color = state.get("personal_color")
    previous_recommendations = state.get("previous_recommendations") or []
    detected_style = state.get("detected_style")
    applied_style_key = state.get("applied_style_key")
    selected_mood = state.get("selected_mood")
    selected_mood_keywords = state.get("selected_mood_keywords") or []

    if detected_style:
        style_code = detected_style.get("style_code")
    elif applied_style_key:
        style_code = applied_style_key
    else:
        style_code = _find_style_code_from_message(
            user_message=user_message,
            previous_recommendations=previous_recommendations,
            category=category,
        )

    detected_style_name = ""
    makeup_group = None
    if detected_style:
        detected_style_name = detected_style.get("style_name", "")
        makeup_group = detected_style.get("makeup_group")

    # 이미지 분석 결과가 있으면 query 구성 요소를 보강한다.
    image_analysis = state.get("image_analysis")
    image_visual_features: list[str] = state.get("image_visual_features") or []
    rag_query_text = ""
    if image_analysis:
        if not style_code:
            candidates = image_analysis.get("style_code_candidates") or []
            if candidates:
                style_code = candidates[0]
        if not detected_style_name:
            detected_style_name = image_analysis.get("detected_style_name") or ""
        rag_query_text = image_analysis.get("rag_query_text") or ""

    image_features_text = " ".join(image_visual_features)

    mood_text = " ".join(selected_mood_keywords)

    if category == CATEGORY_MAKEUP:
        query = (
            f"{gender or ''} {personal_color or ''} 퍼스널컬러 "
            f"{detected_style_name} "
            f"{selected_mood or ''} "
            f"{mood_text} "
            f"{rag_query_text} "
            f"{image_features_text} "
            f"{user_message}"
        ).strip()
        retrieve_kwargs = {
            "query": query,
            "category": CATEGORY_MAKEUP,
            "gender": gender,
            "personal_color": personal_color,
            "makeup_group": makeup_group,
            "style_code": style_code,
            "k": 3,
        }
    else:
        query = (
            f"{gender or ''} {face_shape or ''} 얼굴형 "
            f"{face_proportion or ''} 삼정 비율 "
            f"{detected_style_name} "
            f"{selected_mood or ''} "
            f"{mood_text} "
            f"{rag_query_text} "
            f"{image_features_text} "
            f"{user_message}"
        ).strip()

        retrieve_kwargs = {
            "query": query,
            "category": CATEGORY_HAIR,
            "gender": gender,
            "face_shape": face_shape,
            "face_proportion": face_proportion,
            "style_code": style_code,
            "k": 3,
        }

    try:
        retrieval_result = retrieve_docs(**retrieve_kwargs)

        state["retrieval_result"] = retrieval_result
        state["retrieval_info"] = {
            "category": category,
            "target_type": state.get("target_type"),
            "applied_style_key": applied_style_key,
            "selected_mood_id": state.get("selected_mood_id"),
            "selected_mood": selected_mood,
            "retrieved_count": retrieval_result.retrieved_count,
            "fallback_stage": retrieval_result.fallback_stage
            if retrieval_result.fallback_stage is not None
            else "none",
            "used_filter": retrieval_result.used_filter,
            "intent_debug": state.get("intent_debug"),
        }

    except Exception as exc:
        state["retrieval_result"] = RetrievalResult(
            query=query,
            documents=[],
            retrieved_count=0,
            fallback_stage=None,
            used_filter={},
        )
        state["retrieval_info"] = {
            "category": category,
            "target_type": state.get("target_type"),
            "applied_style_key": applied_style_key,
            "selected_mood_id": state.get("selected_mood_id"),
            "selected_mood": selected_mood,
            "retrieved_count": 0,
            "fallback_stage": "none",
            "intent_debug": state.get("intent_debug"),
        }
        state["error"] = f"retrieval_failed: {exc}"

    return state


def generate_answer_node(state: ChatbotState) -> ChatbotState:
    """
    ChatGenerationInput을 구성하고 generate_chat_answer()로 최종 답변을 생성한다.
    """

    if state.get("error") in {"missing_analysis", "missing_applied_style"}:
        return state

    if state.get("needs_clarification"):
        return state

    retrieval_result = state.get("retrieval_result")

    if retrieval_result is None:
        retrieval_result = RetrievalResult(
            query=state.get("user_message", ""),
            documents=[],
            retrieved_count=0,
            fallback_stage=None,
            used_filter={},
        )

    user_profile = dict(state.get("user_profile") or {})

    if state.get("target_type"):
        user_profile["target_type"] = state.get("target_type")

    if state.get("applied_style_key"):
        user_profile["applied_style_key"] = state.get("applied_style_key")

    if state.get("selected_mood"):
        user_profile["selected_mood"] = state.get("selected_mood")
        user_profile["selected_mood_id"] = state.get("selected_mood_id")
        user_profile["selected_mood_keywords"] = state.get("selected_mood_keywords", [])

    generation_input = ChatGenerationInput(
        user_message=state.get("user_message", ""),
        gender=state.get("gender", ""),
        face_shape=state.get("face_shape", ""),
        face_proportion=state.get("face_proportion", ""),
        personal_color=state.get("personal_color"),
        previous_analysis=state.get("previous_analysis"),
        previous_recommendations=state.get("previous_recommendations") or [],
        user_profile=user_profile,
        chat_history=state.get("chat_history") or [],
        retrieval_result=retrieval_result,
        intent=state.get("intent"),
        category=state.get("category"),
        detected_style=state.get("detected_style"),
        detected_style_is_recommended=state.get(
            "detected_style_is_recommended",
            False,
        ),
        selected_recommendation=state.get("selected_recommendation"),
    )

    generation_result = generate_chat_answer(generation_input)

    state["answer"] = generation_result.answer
    state["retrieval_result"] = generation_result.retrieval_result
    state["retrieval_info"] = {
        "category": state.get("category"),
        "target_type": state.get("target_type"),
        "applied_style_key": state.get("applied_style_key"),
        "selected_mood_id": state.get("selected_mood_id"),
        "selected_mood": state.get("selected_mood"),
        "retrieved_count": generation_result.retrieval_result.retrieved_count,
        "fallback_stage": generation_result.retrieval_result.fallback_stage
        if generation_result.retrieval_result.fallback_stage is not None
        else "none",
        "used_filter": generation_result.retrieval_result.used_filter,
        "model_name": generation_result.model_name,
        "intent_debug": state.get("intent_debug"),
    }

    return state


def update_memory(state: ChatbotState) -> ChatbotState:
    """
    답변 생성 후 chat_history와 user_profile을 업데이트한다.
    """

    user_message = state.get("user_message", "")
    answer = state.get("answer", "")

    updated_chat_history = append_chat_history(
        chat_history=state.get("chat_history") or [],
        user_message=user_message,
        assistant_answer=answer,
    )

    new_preferences = extract_simple_user_preferences(user_message)

    # pending_selection: None이면 user_profile에서도 제거
    new_preferences["pending_selection"] = state.get("pending_selection")

    if state.get("selected_mood"):
        new_preferences["selected_mood"] = state.get("selected_mood")
        new_preferences["selected_mood_id"] = state.get("selected_mood_id")
        new_preferences["selected_mood_keywords"] = state.get("selected_mood_keywords", [])
        new_preferences["pending_selection"] = None

    # outfit 관련 필드 보존
    if state.get("outfit_intent"):
        new_preferences["outfit_intent"] = state.get("outfit_intent")
    if state.get("outfit_context"):
        new_preferences["outfit_context"] = state.get("outfit_context")
    if state.get("outfit_options"):
        new_preferences["outfit_options"] = state.get("outfit_options")
    if state.get("selected_outfit_option"):
        new_preferences["selected_outfit_option"] = state.get("selected_outfit_option")
    # pending_outfit_synthesis: 명시적으로 None이 되면 제거, 값이 있으면 저장
    pending_synthesis = state.get("pending_outfit_synthesis")
    if "pending_outfit_synthesis" in state:
        new_preferences["pending_outfit_synthesis"] = pending_synthesis

    if "pending_retouch" in state:
        new_preferences["pending_retouch"] = state.get("pending_retouch")

    # 최근 생성 이미지 URL 갱신 (outfit synthesis > retouch 순서)
    latest_img = (
        state.get("outfit_result_image_url")
        or state.get("retouch_result_image_url")
        or state.get("retouched_image_url")
    )
    if latest_img:
        new_preferences["latest_generated_image_url"] = latest_img

    # outfit synthesis 관련 필드 보존
    if state.get("outfit_occasion"):
        new_preferences["outfit_occasion"] = state.get("outfit_occasion")
    if state.get("outfit_synthesis_source_image"):
        new_preferences["outfit_synthesis_source_image"] = state.get("outfit_synthesis_source_image")
    if "outfit_synthesis_payload" in state:
        new_preferences["outfit_synthesis_payload"] = state.get("outfit_synthesis_payload")

    updated_user_profile = merge_user_profile(
        user_profile=state.get("user_profile") or {},
        new_preferences=new_preferences,
    )

    state["updated_chat_history"] = updated_chat_history
    state["updated_user_profile"] = updated_user_profile

    return state


# ---------------------------------------------------------------------------
# pending_selection 라우터 노드
# ---------------------------------------------------------------------------

def resolve_pending_selection(state: ChatbotState) -> ChatbotState:
    """
    user_profile에 저장된 pending_selection과 outfit 관련 필드를
    state로 복원한다.
    """
    user_profile = state.get("user_profile") or {}

    if not state.get("pending_selection"):
        pending = user_profile.get("pending_selection")
        if pending:
            state["pending_selection"] = pending

    if not state.get("outfit_options"):
        outfit_options = user_profile.get("outfit_options")
        if outfit_options:
            state["outfit_options"] = outfit_options

    if not state.get("pending_outfit_synthesis"):
        pending_synthesis = user_profile.get("pending_outfit_synthesis")
        if pending_synthesis:
            state["pending_outfit_synthesis"] = pending_synthesis

    if not state.get("outfit_intent"):
        outfit_intent = user_profile.get("outfit_intent")
        if outfit_intent:
            state["outfit_intent"] = outfit_intent

    if not state.get("outfit_context"):
        outfit_context = user_profile.get("outfit_context")
        if outfit_context:
            state["outfit_context"] = outfit_context

    if not state.get("pending_retouch"):
        pending_retouch = user_profile.get("pending_retouch")
        if pending_retouch:
            state["pending_retouch"] = pending_retouch

    # outfit synthesis 관련 필드 복원
    if not state.get("outfit_synthesis_source_image"):
        v = user_profile.get("outfit_synthesis_source_image")
        if v:
            state["outfit_synthesis_source_image"] = v

    if not state.get("outfit_synthesis_payload"):
        v = user_profile.get("outfit_synthesis_payload")
        if v:
            state["outfit_synthesis_payload"] = v

    if not state.get("outfit_occasion"):
        v = user_profile.get("outfit_occasion")
        if v:
            state["outfit_occasion"] = v

    if not state.get("latest_generated_image_url"):
        v = user_profile.get("latest_generated_image_url")
        if v:
            state["latest_generated_image_url"] = v

    return state


# ---------------------------------------------------------------------------
# outfit 전제조건 확인
# ---------------------------------------------------------------------------

def check_hair_makeup_ready(state: ChatbotState) -> ChatbotState:
    """헤어/메이크업 추천이 모두 완료됐는지 확인한다."""
    previous_recommendations = state.get("previous_recommendations") or []

    has_hair = any(r.get("category") == CATEGORY_HAIR for r in previous_recommendations)
    has_makeup = any(r.get("category") == CATEGORY_MAKEUP for r in previous_recommendations)

    if not (has_hair and has_makeup):
        state["outfit_prerequisites_met"] = False
        state["answer"] = (
            "아직 헤어와 메이크업 추천 결과가 없어 의상 추천을 진행하기 어려워요.\n"
            "먼저 헤어와 메이크업 분석을 완료한 뒤 의상 추천을 도와드릴게요."
        )
        state["retrieval_result"] = RetrievalResult(
            query=state.get("user_message", ""),
            documents=[],
            retrieved_count=0,
            fallback_stage=None,
            used_filter={},
        )
        state["retrieval_info"] = {
            "retrieved_count": 0,
            "fallback_stage": "none",
            "used_filter": {},
            "skipped_rag": True,
            "skip_reason": "outfit_prerequisites_not_met",
        }
        return state

    state["outfit_prerequisites_met"] = True
    intent = state.get("intent")
    state["outfit_intent"] = intent

    # outfit_event_coordination: 메시지에서 상황 추출
    if intent == INTENT_OUTFIT_EVENT_COORDINATION and not state.get("outfit_context"):
        extracted = _extract_outfit_context_from_message(state.get("user_message", ""))
        state["outfit_context"] = extracted

    return state


# ---------------------------------------------------------------------------
# outfit 이미지 분석
# ---------------------------------------------------------------------------

def analyze_outfit_image(state: ChatbotState) -> ChatbotState:
    """
    의상 이미지를 vision LLM으로 분석한다. 현재는 stub.
    """
    image_url = state.get("image_url")
    if not image_url:
        return state

    # TODO: Gemini Vision API로 의상 이미지 분석 연동
    state["outfit_image_analysis"] = {
        "outfit_type": "",
        "colors": [],
        "silhouette": "",
        "formality": "",
        "style_mood": [],
        "match_points": [],
        "risk_points": [],
        "confidence": "low",
    }
    return state


# ---------------------------------------------------------------------------
# outfit 상황 선택 요청
# ---------------------------------------------------------------------------

_OUTFIT_CONTEXT_OPTIONS = [
    {"id": "daily", "label": "데일리룩"},
    {"id": "date", "label": "데이트룩"},
    {"id": "wedding_guest", "label": "결혼식 하객룩"},
    {"id": "office", "label": "출근/면접룩"},
    {"id": "formal", "label": "격식 있는 자리"},
    {"id": "casual", "label": "꾸안꾸 캐주얼"},
]


def ask_outfit_context_selection(state: ChatbotState) -> ChatbotState:
    """상황이 없는 일반 의상 추천 질문에서 상황 선택 버튼을 제시한다."""
    state["outfit_intent"] = INTENT_OUTFIT_RECOMMENDATION
    state["answer"] = "어떤 상황에 맞춰 추천해드릴까요?"
    state["pending_selection"] = PENDING_OUTFIT_CONTEXT
    state["selection"] = {
        "type": PENDING_OUTFIT_CONTEXT,
        "options": _OUTFIT_CONTEXT_OPTIONS,
    }
    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": "pending_outfit_context",
    }
    return state


# ---------------------------------------------------------------------------
# outfit 상황 선택 완료 처리
# ---------------------------------------------------------------------------

def handle_outfit_context_pending(state: ChatbotState) -> ChatbotState:
    """상황 선택 결과를 outfit_context에 저장한다."""
    selected_option = state.get("selected_option") or {}
    outfit_context = selected_option.get("id")

    state["outfit_context"] = outfit_context
    state["outfit_intent"] = INTENT_OUTFIT_RECOMMENDATION
    state["intent"] = INTENT_OUTFIT_RECOMMENDATION
    state["pending_selection"] = None
    state["selection"] = None
    state["outfit_prerequisites_met"] = True

    return state


# ---------------------------------------------------------------------------
# outfit 답변 생성 (RAG 없이 LLM coordination prompt)
# ---------------------------------------------------------------------------

def generate_outfit_answer(state: ChatbotState) -> ChatbotState:
    """LLM coordination prompt로 의상 추천/판단 답변을 생성한다."""
    previous_recommendations = state.get("previous_recommendations") or []
    hair_recs = [r for r in previous_recommendations if r.get("category") == CATEGORY_HAIR]
    makeup_recs = [r for r in previous_recommendations if r.get("category") == CATEGORY_MAKEUP]

    hair_summary = hair_recs[0] if hair_recs else {}
    makeup_summary = makeup_recs[0] if makeup_recs else {}

    outfit_intent = state.get("outfit_intent") or state.get("intent")

    prompt = build_outfit_coordination_prompt(
        gender=state.get("gender"),
        face_shape=state.get("face_shape"),
        face_proportion=state.get("face_proportion"),
        personal_color=state.get("personal_color"),
        hair_summary=hair_summary,
        makeup_summary=makeup_summary,
        outfit_context=state.get("outfit_context"),
        outfit_image_analysis=state.get("outfit_image_analysis"),
        outfit_intent=outfit_intent,
        user_message=state.get("user_message", ""),
        previous_analysis=state.get("previous_analysis"),
    )

    if os.getenv("RAG_GENERATOR_MODE", "gemini") == "mock":
        answer = "현재는 개발용 mock 의상 추천 응답입니다."
        outfit_options: list[dict] = [
            {"id": "look_1", "label": "모크 룩 1", "description": "개발용 의상 후보", "colors": [], "items": [], "avoid": []},
            {"id": "look_2", "label": "모크 룩 2", "description": "개발용 의상 후보", "colors": [], "items": [], "avoid": []},
        ]
        if outfit_intent == INTENT_OUTFIT_FIT_CHECK:
            outfit_options = [{"id": "uploaded_outfit", "label": "업로드한 의상", "source": "image"}]
    else:
        chat_model = get_chat_model()
        response = invoke_with_retry(chat_model, prompt)
        content = normalize_model_content(getattr(response, "content", response))
        answer, outfit_options = parse_outfit_response(content, outfit_intent)

    state["outfit_options"] = outfit_options
    state["outfit_intent"] = outfit_intent

    if outfit_intent == INTENT_OUTFIT_FIT_CHECK:
        synthesis_offer = "이 의상을 고객님 사진에 맞춰 합성해서 보여드릴까요?"
    else:
        synthesis_offer = "추천드린 의상 중 하나를 고객님 사진에 합성해서 보여드릴까요?"

    state["answer"] = f"{answer}\n\n{synthesis_offer}"
    state["pending_selection"] = PENDING_OUTFIT_SYNTHESIS_CONFIRMATION
    state["selection"] = {
        "type": PENDING_OUTFIT_SYNTHESIS_CONFIRMATION,
        "options": [
            {"id": "confirm_outfit_synthesis", "label": "합성 진행하기"},
            {"id": "cancel_outfit_synthesis", "label": "취소하기"},
        ],
    }

    user_profile = state.get("user_profile") or {}
    state["pending_outfit_synthesis"] = {
        "question_type": outfit_intent,
        "outfit_context": state.get("outfit_context"),
        "user_image_url": user_profile.get("user_image_url"),
        "outfit_image_url": state.get("image_url") if outfit_intent == INTENT_OUTFIT_FIT_CHECK else None,
        "selected_outfit_option": None,
        "outfit_options": outfit_options,
        "hair_summary": hair_summary,
        "makeup_summary": makeup_summary,
        "user_profile": {
            "gender": state.get("gender"),
            "face_shape": state.get("face_shape"),
            "face_proportion": state.get("face_proportion"),
            "personal_color": state.get("personal_color"),
        },
        "original_user_message": state.get("user_message", ""),
    }

    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": outfit_intent,
    }

    return state


# ---------------------------------------------------------------------------
# 합성 확인 버튼 처리
# ---------------------------------------------------------------------------

def handle_synthesis_confirmation(state: ChatbotState) -> ChatbotState:
    """합성 진행하기 / 취소하기 선택을 처리한다."""
    selected_option = state.get("selected_option") or {}
    selected_id = selected_option.get("id")

    if selected_id == "cancel_outfit_synthesis":
        state["outfit_synthesis_action"] = "cancel"
        state["pending_outfit_synthesis"] = None
        state["pending_selection"] = None
        state["selection"] = None
        state["outfit_options"] = []
        state["answer"] = "의상 합성을 취소했습니다. 다른 궁금한 점이 있으시면 언제든 말씀해 주세요."
        state["retrieval_result"] = RetrievalResult(
            query=state.get("user_message", ""),
            documents=[],
            retrieved_count=0,
            fallback_stage=None,
            used_filter={},
        )
        state["retrieval_info"] = {
            "retrieved_count": 0,
            "fallback_stage": "none",
            "used_filter": {},
            "skipped_rag": True,
            "skip_reason": "outfit_synthesis_cancelled",
        }
        return state

    # confirm 선택
    outfit_options = state.get("outfit_options") or (state.get("pending_outfit_synthesis") or {}).get("outfit_options") or []
    state["pending_selection"] = None
    state["selection"] = None

    if len(outfit_options) > 1:
        state["outfit_synthesis_action"] = "select_option"
    else:
        # 단일 의상이면 바로 선택 처리
        if outfit_options:
            single = outfit_options[0]
            state["selected_outfit_option"] = single
            pending_synthesis = dict(state.get("pending_outfit_synthesis") or {})
            pending_synthesis["selected_outfit_option"] = single
            state["pending_outfit_synthesis"] = pending_synthesis
        state["outfit_synthesis_action"] = "check_image"

    return state


# ---------------------------------------------------------------------------
# 의상 후보 선택 요청
# ---------------------------------------------------------------------------

def ask_outfit_option_selection(state: ChatbotState) -> ChatbotState:
    """추천된 의상 후보 중 합성할 룩을 선택하도록 요청한다."""
    outfit_options = state.get("outfit_options") or []

    state["answer"] = "어떤 룩으로 합성할까요?"
    state["pending_selection"] = PENDING_OUTFIT_OPTION_SELECTION
    state["selection"] = {
        "type": PENDING_OUTFIT_OPTION_SELECTION,
        "options": [{"id": opt["id"], "label": opt["label"]} for opt in outfit_options],
    }
    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": "pending_outfit_option_selection",
    }
    return state


# ---------------------------------------------------------------------------
# 의상 후보 선택 완료 처리
# ---------------------------------------------------------------------------

def handle_outfit_option_pending(state: ChatbotState) -> ChatbotState:
    """선택된 의상 후보를 selected_outfit_option에 저장한다."""
    selected_option = state.get("selected_option") or {}
    selected_id = selected_option.get("id")

    outfit_options = (
        state.get("outfit_options")
        or (state.get("pending_outfit_synthesis") or {}).get("outfit_options")
        or []
    )
    selected = next((opt for opt in outfit_options if opt.get("id") == selected_id), None)

    state["selected_outfit_option"] = selected
    state["pending_selection"] = None
    state["selection"] = None

    if selected:
        pending_synthesis = dict(state.get("pending_outfit_synthesis") or {})
        pending_synthesis["selected_outfit_option"] = selected
        state["pending_outfit_synthesis"] = pending_synthesis

    return state


# ---------------------------------------------------------------------------
# 유저 사진 확인
# ---------------------------------------------------------------------------

def check_user_image_for_synthesis(state: ChatbotState) -> ChatbotState:
    """
    합성에 사용할 유저 사진 URL을 확인한다.
    헤어/메이크업 합성 완료 후 저장된 사진을 user_profile에서 가져온다.
    """
    user_profile = state.get("user_profile") or {}
    pending_synthesis = state.get("pending_outfit_synthesis") or {}

    user_image_url = (
        pending_synthesis.get("user_image_url")
        or user_profile.get("user_image_url")
        or user_profile.get("synthesized_image_url")
    )

    if user_image_url:
        pending_synthesis = dict(pending_synthesis)
        pending_synthesis["user_image_url"] = user_image_url
        state["pending_outfit_synthesis"] = pending_synthesis
        return state

    # 사진 없음
    state["answer"] = (
        "합성을 진행하려면 고객님 사진이 필요해요.\n"
        "현재 버전에서는 사진 업로드 후 합성 기능을 사용할 수 있어요.\n"
        "사진 업로드 기능이 연결되면 바로 합성을 진행할 수 있도록 준비해둘게요."
    )
    state["pending_selection"] = PENDING_OUTFIT_USER_IMAGE_REQUIRED
    state["selection"] = None
    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": "outfit_user_image_required",
    }
    return state


# ---------------------------------------------------------------------------
# 유저 사진 대기 처리
# ---------------------------------------------------------------------------

def handle_outfit_user_image_pending(state: ChatbotState) -> ChatbotState:
    """사진 업로드 대기 상태에서 image_url이 들어오면 합성을 이어서 진행한다."""
    image_url = state.get("image_url")

    if image_url:
        pending_synthesis = dict(state.get("pending_outfit_synthesis") or {})
        pending_synthesis["user_image_url"] = image_url
        state["pending_outfit_synthesis"] = pending_synthesis
        state["pending_selection"] = None
        return state

    state["answer"] = (
        "합성을 진행하려면 고객님 사진이 필요해요.\n"
        "얼굴과 상반신이 잘 보이는 사진을 업로드해 주세요."
    )
    state["pending_selection"] = PENDING_OUTFIT_USER_IMAGE_REQUIRED
    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": "outfit_user_image_required",
    }
    return state


# ---------------------------------------------------------------------------
# 의상 합성 실행
# ---------------------------------------------------------------------------

def run_outfit_synthesis(state: ChatbotState) -> ChatbotState:
    """
    의상 합성을 실행한다. 현재는 stub — 실제 합성 모듈 연동 시 교체한다.
    """
    pending_synthesis = state.get("pending_outfit_synthesis") or {}
    selected_outfit = pending_synthesis.get("selected_outfit_option") or {}
    outfit_label = selected_outfit.get("label", "선택한 의상")

    # TODO: 실제 이미지 합성 API 연동
    state["answer"] = (
        f"'{outfit_label}'으로 합성을 준비 중이에요. "
        "합성 기능은 추후 연결 예정입니다."
    )
    state["pending_selection"] = None
    state["selection"] = None
    state["pending_outfit_synthesis"] = None
    state["outfit_options"] = []
    state["selected_outfit_option"] = None
    state["outfit_synthesis_action"] = None
    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": "outfit_synthesis",
    }
    return state


# ---------------------------------------------------------------------------
# 대화 기억 / 후속 추천 노드
# ---------------------------------------------------------------------------

def answer_memory_recall(state: ChatbotState) -> ChatbotState:
    """chat_history에서 가장 최근 user 발화를 찾아 그대로 알려준다."""
    chat_history = state.get("chat_history") or []

    last_user_msg: str | None = None
    for msg in reversed(chat_history):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "").strip()
            break

    if last_user_msg:
        state["answer"] = f'방금 "{last_user_msg}"이라고 하셨어요.'
    else:
        state["answer"] = "이전 대화 기록이 없어서 기억하지 못해요."

    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "skipped_rag": True,
        "skip_reason": "memory_recall",
    }
    return state


def answer_followup_recommendation(state: ChatbotState) -> ChatbotState:
    """previous_recommendations에서 아직 언급 안 된 대안 스타일을 안내한다."""
    chat_history = state.get("chat_history") or []
    previous_recommendations = state.get("previous_recommendations") or []
    user_message = state.get("user_message", "")

    category = state.get("category") or detect_question_category(user_message)

    last_ai_answer = ""
    for msg in reversed(chat_history):
        if msg.get("role") == "assistant":
            last_ai_answer = msg.get("content", "")
            break

    candidates = [r for r in previous_recommendations if r.get("category") == category]

    alternatives = [
        r for r in candidates
        if not (r.get("style_name") and r["style_name"] in last_ai_answer)
    ]

    category_label = "메이크업" if category == CATEGORY_MAKEUP else "헤어스타일"

    if alternatives:
        names = [r.get("style_name", "") for r in alternatives[:3] if r.get("style_name")]
        name_str = ", ".join(names)
        state["answer"] = (
            f"다른 방향으로는 {name_str}도 볼 수 있어요.\n"
            f"각 {category_label}의 분위기가 조금씩 달라서 원하시는 느낌에 맞게 선택해 보세요."
        )
    elif candidates:
        state["answer"] = "추천드린 스타일들이 이미 전부 안내된 것 같아요. 다른 점이 궁금하시면 말씀해 주세요!"
    else:
        state["answer"] = f"현재 추천 목록에 다른 {category_label}이 없어요. 원하시는 조건이 있으면 더 알려주세요!"

    state["retrieval_result"] = RetrievalResult(
        query=user_message,
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "skipped_rag": True,
        "skip_reason": "followup_recommendation",
    }
    return state


def _resolve_selected_style_for_category(state: ChatbotState) -> dict | None:
    """
    현재 category에 맞는 선택 스타일을 상태 또는 chat_history에서 복원한다.

    복원 우선순위:
    1. check_analysis_exists가 이미 설정한 selected_recommendation (category 필터 적용됨)
    2. applied_style_key로 category 필터링된 previous_recommendations 매칭
    3. category 추천이 1개뿐이면 그것을 선택 스타일로 사용
    4. chat_history assistant 메시지에서 "'스타일명' 스타일에 대해" 패턴 추출
    5. None (list 응답으로 fallback)

    메이크업 채팅이면 hair 추천, 헤어 채팅이면 makeup 추천을 절대 반환하지 않는다.
    """
    target_type = _normalize_target_type(state.get("target_type"))
    user_message = state.get("user_message", "")
    current_category = (
        target_type
        or state.get("category")
        or detect_question_category(user_message)
        or infer_category_from_chat_history(state.get("chat_history") or [])
        or CATEGORY_HAIR
    )

    if not current_category:
        return None

    # 1. check_analysis_exists에서 이미 설정된 selected_recommendation 우선 사용.
    #    _find_recommended_style_by_key는 category 필터 후 반환하므로 "category" 키가 없어도 안전.
    selected_recommendation = state.get("selected_recommendation")
    if selected_recommendation:
        rec_category = selected_recommendation.get("category")
        if rec_category is None or rec_category == current_category:
            return selected_recommendation

    # 2. category 필터링된 추천 목록
    previous_recommendations = state.get("previous_recommendations") or []
    category_recs = [r for r in previous_recommendations if r.get("category") == current_category]

    # 3. applied_style_key로 category_recs에서 매칭 (style_code가 없고 style_name이 키인 경우 포함)
    applied_style_key = state.get("applied_style_key")
    if applied_style_key:
        for r in category_recs:
            candidate_keys = {
                r.get("style_code"),
                r.get("style_key"),
                r.get("applied_style_key"),
                r.get("style_name"),
                r.get("makeup_group"),
            }
            if applied_style_key in {str(k) for k in candidate_keys if k}:
                return r

    # 4. category 추천이 1개뿐이면 그것이 현재 상담 스타일
    if len(category_recs) == 1:
        return category_recs[0]

    # 5. chat_history의 assistant 메시지에서 "'스타일명' 스타일에 대해" 패턴 추출
    for turn in state.get("chat_history") or []:
        if turn.get("role") == "user":
            continue
        text = turn.get("content") or turn.get("assistant") or ""
        match = re.search(r"'([^']+)' 스타일에 대해", text)
        if match:
            name = match.group(1)
            for r in category_recs:
                if r.get("style_name") == name:
                    return r
            if name:
                return {"category": current_category, "style_name": name}

    return None


def handle_recommendation_recall(state: ChatbotState) -> ChatbotState:
    """
    추천 회상 질문에 대해 현재 category의 추천만 필터링해 상태 기반으로 답변한다.
    RAG 검색을 거치지 않는다.

    메이크업 채팅에서는 반드시 메이크업 추천만, 헤어 채팅에서는 헤어 추천만 반환한다.
    """
    user_message = state.get("user_message", "")
    target_type = _normalize_target_type(state.get("target_type"))
    current_category = target_type or state.get("category") or detect_question_category(user_message)
    personal_color = state.get("personal_color") or ""

    previous_recommendations = state.get("previous_recommendations") or []
    filtered_recs = [
        r for r in previous_recommendations
        if r.get("category") == current_category
    ]

    resolved_style = _resolve_selected_style_for_category(state)

    if current_category == CATEGORY_MAKEUP:
        chat_label = "메이크업"
        style_label = "메이크업"
        no_rec_msg = (
            "현재 메이크업 채팅에서 확인할 수 있는 추천 메이크업 정보가 없어요.\n"
            "분석 결과에서 메이크업 추천을 다시 확인해 주세요."
        )
    else:
        chat_label = "헤어"
        style_label = "헤어스타일"
        no_rec_msg = (
            "현재 헤어 채팅에서 확인할 수 있는 추천 헤어 정보가 없어요.\n"
            "분석 결과에서 헤어 추천을 다시 확인해 주세요."
        )

    if resolved_style:
        style_name = resolved_style.get("style_name", "")
        if current_category == CATEGORY_MAKEUP:
            if personal_color:
                state["answer"] = (
                    f"현재 메이크업 채팅에서 선택하신 추천 스타일은 '{style_name}'이에요.\n"
                    f"{personal_color} 퍼스널컬러에 맞춰 자연스럽고 조화롭게 연출하는 메이크업 스타일입니다."
                )
            else:
                state["answer"] = (
                    f"현재 메이크업 채팅에서 선택하신 추천 스타일은 '{style_name}'이에요.\n"
                    "해당 스타일에 대해 더 궁금한 점이 있으시면 말씀해 주세요."
                )
        else:
            state["answer"] = (
                f"현재 헤어 채팅에서 선택하신 추천 스타일은 '{style_name}'이에요.\n"
                "고객님의 얼굴형과 삼정 비율을 기준으로 추천된 헤어스타일입니다."
            )
    elif filtered_recs:
        names = [r.get("style_name", "") for r in filtered_recs if r.get("style_name")]
        name_str = ", ".join(names)
        if current_category == CATEGORY_MAKEUP:
            state["answer"] = (
                f"현재 메이크업 채팅에서 추천받은 {style_label}은 {name_str}이에요.\n"
                "현재 선택하신 스타일이 있다면 해당 스타일을 기준으로 더 자세히 상담해드릴 수 있어요."
            )
        else:
            state["answer"] = (
                f"현재 {chat_label} 채팅에서 추천받은 {style_label}은 {name_str}이에요.\n"
                "현재 선택하신 스타일을 기준으로 어울림이나 손질법을 더 자세히 안내해드릴 수 있어요."
            )
    else:
        state["answer"] = no_rec_msg

    state["retrieval_result"] = RetrievalResult(
        query=user_message,
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "skipped_rag": True,
        "skip_reason": "recommendation_recall",
    }
    return state


# ---------------------------------------------------------------------------
# New outfit flow — 이미지 업로드 없이 최근 생성 이미지 기반
# ---------------------------------------------------------------------------

def _no_rag_result(state: ChatbotState, reason: str) -> None:
    state["retrieval_result"] = RetrievalResult(
        query=state.get("user_message", ""),
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )
    state["retrieval_info"] = {
        "retrieved_count": 0,
        "fallback_stage": "none",
        "used_filter": {},
        "skipped_rag": True,
        "skip_reason": reason,
    }


def resolve_latest_generated_image(state: ChatbotState) -> str | None:
    """
    최근 생성된 이미지 URL을 다음 우선순위로 반환한다.
    1. outfit_result_image_url (이번 턴 의상 합성 결과)
    2. retouch_result_image_url / retouched_image_url (이번 턴 리터치 결과)
    3. latest_generated_image_url (user_profile 경유로 이전 턴에서 복원된 URL)
    4. sim_image_url (프론트엔드가 전달한 GAN 시뮬레이션 결과)
    5. user_profile.current_image_url / analysis_image_url
    """
    user_profile = state.get("user_profile") or {}
    return (
        state.get("outfit_result_image_url")
        or state.get("retouch_result_image_url")
        or state.get("retouched_image_url")
        or state.get("latest_generated_image_url")
        or user_profile.get("latest_generated_image_url")
        or state.get("sim_image_url")
        or user_profile.get("current_image_url")
        or user_profile.get("analysis_image_url")
    )


def _build_beauty_style_for_outfit(state: ChatbotState) -> dict:
    previous_recommendations = state.get("previous_recommendations") or []
    hair_recs = [r for r in previous_recommendations if r.get("category") == CATEGORY_HAIR]
    makeup_recs = [r for r in previous_recommendations if r.get("category") == CATEGORY_MAKEUP]
    user_profile = state.get("user_profile") or {}
    return {
        "selected_hair": hair_recs[0] if hair_recs else {},
        "selected_makeup": makeup_recs[0] if makeup_recs else {},
        "latest_retouch_summary": user_profile.get("retouch_request") or "",
    }


_OUTFIT_ADVICE_CONSTRAINTS = [
    "추천은 실제 착용 가능한 의상 중심으로 한다.",
    "헤어와 메이크업 분위기를 해치지 않는다.",
    "퍼스널컬러와 조화되는 색상을 우선한다.",
    "상황에 맞는 격식 수준을 지킨다.",
    "과도하게 추상적인 설명보다 구체적인 아이템 조합을 제안한다.",
]

_OUTFIT_PRESERVE_CONDITIONS = [
    "얼굴은 변경하지 않는다.",
    "헤어스타일은 변경하지 않는다.",
    "메이크업은 변경하지 않는다.",
    "표정과 포즈는 유지한다.",
    "배경은 최대한 유지한다.",
    "의상만 자연스럽게 변경한다.",
]


def generate_outfit_advice(state: ChatbotState) -> ChatbotState:
    """
    outfit_advice intent — RAG 없이 LLM으로 텍스트 의상 추천을 생성한다.
    이미지가 없어도 분석 정보 기반으로 추천 가능하다.
    """
    user_message = state.get("user_message", "")
    occasion = detect_outfit_occasion(user_message) or state.get("outfit_occasion")
    resolved_image = resolve_latest_generated_image(state)

    payload = {
        "source_image_url": resolved_image,
        "user_profile": {
            "gender": state.get("gender"),
            "face_shape": state.get("face_shape"),
            "face_proportion": state.get("face_proportion"),
            "personal_color": state.get("personal_color"),
            "skin_tone": (state.get("user_profile") or {}).get("skin_tone"),
        },
        "current_beauty_style": _build_beauty_style_for_outfit(state),
        "user_request": {
            "type": INTENT_OUTFIT_ADVICE,
            "occasion": occasion,
            "raw_text": user_message,
        },
        "constraints": _OUTFIT_ADVICE_CONSTRAINTS,
    }

    state["intent"] = INTENT_OUTFIT_ADVICE
    state["outfit_occasion"] = occasion

    if os.getenv("RAG_GENERATOR_MODE", "gemini") == "mock":
        occasion_label = OCCASION_LABELS.get(occasion or "", "상황")
        state["answer"] = (
            f"{occasion_label} 상황에 어울리는 의상 추천입니다. (개발용 mock 응답)\n"
            "아이보리 블라우스 + 베이지 슬랙스 + 라이트 브라운 로퍼 조합을 추천드려요."
        )
    else:
        prompt = build_outfit_advice_prompt(payload)
        chat_model = get_chat_model()
        response = invoke_with_retry(chat_model, prompt)
        state["answer"] = normalize_model_content(getattr(response, "content", response))

    _no_rag_result(state, INTENT_OUTFIT_ADVICE)
    return state


def analyze_outfit_synthesis_request(state: ChatbotState) -> ChatbotState:
    """
    outfit_synthesis intent — 최근 생성 이미지를 확인하고 명확/불명확 요청에 따라 분기한다.
    이미지 없음 → 안내 후 종료.
    명확 요청 → 합성 확인 버튼 제시.
    불명확 요청 → 방향 재질문.
    """
    user_message = state.get("user_message", "")
    resolved_image = resolve_latest_generated_image(state)

    state["intent"] = INTENT_OUTFIT_SYNTHESIS

    # 기준 이미지 없음 → 안내 후 종료
    if not resolved_image:
        state["answer"] = (
            "아직 기준이 되는 스타일 결과 이미지가 없어요.\n"
            "먼저 헤어 또는 메이크업 리터치를 진행한 뒤 의상 합성을 할 수 있어요."
        )
        state["pending_selection"] = None
        state["selection"] = None
        _no_rag_result(state, "outfit_synthesis_no_image")
        return state

    occasion = detect_outfit_occasion(user_message) or state.get("outfit_occasion")
    needs_clarification = is_outfit_clarification_needed(user_message)

    # 방향 불명확 → 재질문
    if needs_clarification and not occasion:
        state["answer"] = (
            "어떤 상황이나 느낌의 의상으로 합성할까요?\n\n"
            "예를 들면:\n- 면접룩\n- 결혼식 하객룩\n- 소개팅룩\n- 나들이룩\n"
            "- 아이보리 블라우스와 베이지 슬랙스"
        )
        state["pending_selection"] = PENDING_OUTFIT_CLARIFICATION
        state["selection"] = None
        state["outfit_synthesis_source_image"] = resolved_image
        _no_rag_result(state, "outfit_synthesis_clarification")
        return state

    # 명확한 요청 → 확인 단계
    occasion_label = OCCASION_LABELS.get(occasion or "", occasion or "상황 정보 없음")
    normalized_request = user_message.strip()

    state["outfit_occasion"] = occasion
    state["outfit_synthesis_source_image"] = resolved_image
    state["outfit_synthesis_payload"] = {
        "source_image_url": resolved_image,
        "user_profile": {
            "gender": state.get("gender"),
            "face_shape": state.get("face_shape"),
            "face_proportion": state.get("face_proportion"),
            "personal_color": state.get("personal_color"),
            "skin_tone": (state.get("user_profile") or {}).get("skin_tone"),
        },
        "current_beauty_style": _build_beauty_style_for_outfit(state),
        "outfit_request": {
            "occasion": occasion,
            "requested_change": normalized_request,
            "raw_text": user_message,
        },
        "preserve": _OUTFIT_PRESERVE_CONDITIONS,
    }

    state["answer"] = (
        f"다음 내용으로 의상 합성을 진행할까요?\n\n"
        f"- 상황: {occasion_label}\n"
        f"- 의상 방향: {normalized_request}\n"
        f"- 기준 이미지: 최근 생성된 스타일 이미지\n"
        f"- 유지 조건: 얼굴, 헤어, 메이크업, 표정, 포즈는 유지"
    )
    state["pending_selection"] = PENDING_OUTFIT_CONFIRMATION
    state["selection"] = {
        "type": PENDING_OUTFIT_CONFIRMATION,
        "options": [
            {"id": "confirm_outfit_synthesis", "label": "의상 합성하기"},
            {"id": "cancel_outfit_synthesis", "label": "취소하기"},
        ],
    }
    _no_rag_result(state, "outfit_synthesis_pending_confirmation")
    return state


def handle_outfit_clarification(state: ChatbotState) -> ChatbotState:
    """
    PENDING_OUTFIT_CLARIFICATION 처리 — 유저가 의상 방향을 입력한 뒤 확인 단계로 이동한다.
    """
    user_message = state.get("user_message", "")
    user_profile = state.get("user_profile") or {}

    resolved_image = (
        state.get("outfit_synthesis_source_image")
        or user_profile.get("outfit_synthesis_source_image")
        or resolve_latest_generated_image(state)
    )

    state["pending_selection"] = None
    state["selection"] = None

    if not resolved_image:
        state["answer"] = (
            "아직 기준이 되는 스타일 결과 이미지가 없어요.\n"
            "먼저 헤어 또는 메이크업 리터치를 진행한 뒤 의상 합성을 할 수 있어요."
        )
        _no_rag_result(state, "outfit_synthesis_no_image")
        return state

    occasion = detect_outfit_occasion(user_message) or state.get("outfit_occasion")
    occasion_label = OCCASION_LABELS.get(occasion or "", user_message[:20] or "상황 정보 없음")
    normalized_request = user_message.strip()

    state["outfit_occasion"] = occasion
    state["outfit_synthesis_source_image"] = resolved_image
    state["outfit_synthesis_payload"] = {
        "source_image_url": resolved_image,
        "user_profile": {
            "gender": state.get("gender"),
            "face_shape": state.get("face_shape"),
            "face_proportion": state.get("face_proportion"),
            "personal_color": state.get("personal_color"),
            "skin_tone": user_profile.get("skin_tone"),
        },
        "current_beauty_style": _build_beauty_style_for_outfit(state),
        "outfit_request": {
            "occasion": occasion,
            "requested_change": normalized_request,
            "raw_text": user_message,
        },
        "preserve": _OUTFIT_PRESERVE_CONDITIONS,
    }

    state["answer"] = (
        f"다음 내용으로 의상 합성을 진행할까요?\n\n"
        f"- 상황: {occasion_label}\n"
        f"- 의상 방향: {normalized_request}\n"
        f"- 기준 이미지: 최근 생성된 스타일 이미지\n"
        f"- 유지 조건: 얼굴, 헤어, 메이크업, 표정, 포즈는 유지"
    )
    state["pending_selection"] = PENDING_OUTFIT_CONFIRMATION
    state["selection"] = {
        "type": PENDING_OUTFIT_CONFIRMATION,
        "options": [
            {"id": "confirm_outfit_synthesis", "label": "의상 합성하기"},
            {"id": "cancel_outfit_synthesis", "label": "취소하기"},
        ],
    }
    _no_rag_result(state, "outfit_clarification_to_confirmation")
    return state


def handle_outfit_confirmation(state: ChatbotState) -> ChatbotState:
    """
    PENDING_OUTFIT_CONFIRMATION 처리 — 확인이면 합성 진행, 취소면 종료한다.
    """
    selected_option = state.get("selected_option") or {}
    selected_id = selected_option.get("id")

    state["pending_selection"] = None
    state["selection"] = None

    if selected_id == "cancel_outfit_synthesis":
        state["outfit_synthesis_action"] = "cancel"
        state["outfit_synthesis_payload"] = None
        state["answer"] = "의상 합성을 취소했습니다. 다른 궁금한 점이 있으시면 말씀해 주세요."
        _no_rag_result(state, "outfit_synthesis_cancelled")
        return state

    state["outfit_synthesis_action"] = "confirm"
    _no_rag_result(state, "outfit_synthesis_confirmed")
    return state


def run_new_outfit_synthesis(state: ChatbotState) -> ChatbotState:
    """
    의상 합성 실행 — Gemini imagen으로 최근 생성 이미지에 의상만 변경한다.
    """
    import logging
    logger = logging.getLogger(__name__)

    payload = state.get("outfit_synthesis_payload") or {}
    source_image_url = payload.get("source_image_url") or resolve_latest_generated_image(state)

    state["outfit_synthesis_action"] = None
    state["outfit_synthesis_payload"] = None

    if not source_image_url:
        state["answer"] = "합성에 사용할 기준 이미지를 찾을 수 없어요."
        _no_rag_result(state, "outfit_synthesis_no_image")
        return state

    if os.getenv("RAG_GENERATOR_MODE", "gemini") == "mock":
        state["answer"] = "의상 합성이 완료됐어요. (개발용 mock 응답)"
        state["outfit_result_image_url"] = None
        _no_rag_result(state, "outfit_synthesis_mock")
        return state

    try:
        prompt_text = build_outfit_synthesis_prompt_text(payload)
        result_url = call_gemini_image_synthesis(source_image_url, prompt_text)
        state["outfit_result_image_url"] = result_url
        state["answer"] = (
            "의상 합성이 완료됐어요. 아래 이미지를 확인해 주세요.\n"
            "더 수정이 필요하시면 말씀해 주세요."
        )
    except Exception as exc:
        logger.error("[run_new_outfit_synthesis] Gemini 호출 실패: %s", exc, exc_info=True)
        state["outfit_result_image_url"] = None
        state["answer"] = "의상 합성 중 오류가 발생했어요. 잠시 후 다시 시도해 주세요."

    _no_rag_result(state, "outfit_synthesis_done")
    return state
