from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Any

import requests as _requests
from django.conf import settings
from google import genai
from google.genai import types

from backend.app.rag.chatbot_rag.intents import (
    PENDING_RETOUCH_CLARIFICATION,
    PENDING_RETOUCH_CONFIRMATION,
    PENDING_RETOUCH_IMAGE_REQUIRED,
)
from backend.app.rag.chatbot_rag.state import ChatbotState
from backend.app.rag.rag_core.config import GEMINI_API_KEY, GEMINI_IMAGE_MODEL
from backend.app.rag.rag_core.schemas import RetrievalResult

logger = logging.getLogger(__name__)


def _empty_retrieval(query: str) -> RetrievalResult:
    return RetrievalResult(
        query=query,
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )


_EMPTY_INFO: dict[str, Any] = {
    "retrieved_count": 0,
    "fallback_stage": "none",
    "used_filter": {},
    "skipped_rag": True,
}

_CLARIFICATION_OPTIONS = [
    {"id": "recommended_hair", "label": "추천된 헤어스타일로 변경"},
    {"id": "recommended_makeup", "label": "추천된 메이크업으로 변경"},
    {"id": "hair_partial", "label": "앞머리/볼륨/컬감만 수정"},
    {"id": "makeup_partial", "label": "립/치크/아이 메이크업만 수정"},
    {"id": "overall_natural", "label": "전체적으로 자연스럽게 보정"},
]

_AMBIGUOUS_PHRASES = {
    "예쁘게 바꿔줘",
    "좀 수정해줘",
    "수정해줘",
    "메이크업 바꿔줘",
    "머리 바꿔줘",
    "자연스럽게 해줘",
}

_CLEAR_HINTS = [
    "선택",
    "추천",
    "리프",
    "시스루",
    "앞머리",
    "볼륨",
    "컬",
    "립",
    "치크",
    "아이",
    "코랄",
    "로즈",
    "진하게",
    "피부톤",
    "보정",
]


def _source_image_url(state: ChatbotState) -> str | None:
    user_profile = state.get("user_profile") or {}
    return (
        state.get("image_url")
        or state.get("sim_image_url")
        or user_profile.get("user_image_url")
        or user_profile.get("synthesized_image_url")
    )


def _infer_target(text: str) -> str:
    if any(word in text for word in ["헤어", "머리", "앞머리", "볼륨", "컬", "리프", "시스루"]):
        return "hair"
    if any(word in text for word in ["메이크업", "화장", "립", "치크", "아이", "코랄", "로즈"]):
        return "makeup"
    if any(word in text for word in ["피부", "피부톤", "보정"]):
        return "partial"
    return "overall"


def _selected_style(state: ChatbotState, target: str) -> dict[str, Any] | None:
    selected = state.get("selected_recommendation") or state.get("detected_style")
    if selected:
        return dict(selected)

    category = "makeup" if target == "makeup" else "hair"
    for recommendation in state.get("previous_recommendations") or []:
        if recommendation.get("category") == category:
            return dict(recommendation)
    return None


def _request_from_option(option_id: str, state: ChatbotState) -> dict[str, Any]:
    option_map = {
        "recommended_hair": ("hair", "추천된 헤어스타일을 자연스럽게 적용"),
        "recommended_makeup": ("makeup", "추천된 메이크업을 자연스럽게 적용"),
        "hair_partial": ("hair", "앞머리/볼륨/컬감만 자연스럽게 수정"),
        "makeup_partial": ("makeup", "립/치크/아이 메이크업만 자연스럽게 수정"),
        "overall_natural": ("overall", "전체적으로 자연스럽게 보정"),
    }
    target, requested_change = option_map.get(option_id, ("overall", "전체적으로 자연스럽게 보정"))
    return {
        "target": target,
        "requested_change": requested_change,
        "selected_style": _selected_style(state, target),
    }


def _analyze_text_request(user_message: str, state: ChatbotState) -> tuple[str, dict[str, Any]]:
    text = user_message.strip()
    normalized = text.replace(" ", "").lower()
    compact_ambiguous = {phrase.replace(" ", "").lower() for phrase in _AMBIGUOUS_PHRASES}

    target = _infer_target(text)
    has_clear_hint = any(hint in text for hint in _CLEAR_HINTS)

    if normalized in compact_ambiguous or not has_clear_hint:
        return "ambiguous", {
            "target": target,
            "requested_change": text,
            "selected_style": None,
        }

    return "clear", {
        "target": target,
        "requested_change": text,
        "selected_style": _selected_style(state, target),
    }


def _set_no_rag(state: ChatbotState, reason: str) -> None:
    state["retrieval_result"] = _empty_retrieval(state.get("user_message", ""))
    state["retrieval_info"] = {**_EMPTY_INFO, "skip_reason": reason}


# ---------------------------------------------------------------------------
# Gemini image editing helpers
# ---------------------------------------------------------------------------

def _download_image(url: str) -> tuple[bytes, str]:
    """Download image bytes from URL, with local media path shortcut."""
    media_url: str = settings.MEDIA_URL        # e.g. "/media/"
    media_root: str = str(settings.MEDIA_ROOT)

    # Resolve local Django media paths without an HTTP round-trip
    local_path: str | None = None
    if url.startswith(media_url):
        local_path = os.path.join(media_root, url[len(media_url):])
    else:
        for host in ("http://127.0.0.1:8000", "http://localhost:8000", "http://0.0.0.0:8000"):
            if url.startswith(host + media_url):
                local_path = os.path.join(media_root, url[len(host + media_url):])
                break

    if local_path and os.path.exists(local_path):
        with open(local_path, "rb") as f:
            data = f.read()
        if local_path.lower().endswith(".png"):
            return data, "image/png"
        if local_path.lower().endswith(".webp"):
            return data, "image/webp"
        return data, "image/jpeg"

    resp = _requests.get(url, timeout=30)
    resp.raise_for_status()
    mime = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
    return resp.content, mime


def _build_retouch_prompt(payload: dict[str, Any]) -> str:
    req = payload.get("retouch_request", {}) or {}
    target = req.get("target", "overall")
    change = (req.get("requested_change") or "").strip()
    selected = req.get("selected_style") or {}
    up = payload.get("user_profile", {}) or {}

    style_name = selected.get("style_name")
    style_features = selected.get("style_features") or selected.get("features") or []

    parts: list[str] = [
        "You are a professional beauty retouching AI. "
        "Edit ONLY the specified area of the person in the attached photo. "
        "The person's identity, face shape, facial features, skin tone, expression, "
        "pose, outfit, and background MUST remain exactly the same. "
        "Do NOT replace or alter the person."
    ]

    user_info: list[str] = []
    gender_map = {"남성": "male", "여성": "female"}
    if up.get("gender"):
        user_info.append(f"gender: {gender_map.get(up['gender'], up['gender'])}")
    if up.get("face_shape"):
        user_info.append(f"face shape: {up['face_shape']}")
    if up.get("personal_color"):
        user_info.append(f"personal color season: {up['personal_color']}")
    if up.get("skin_tone"):
        user_info.append(f"skin tone: {up['skin_tone']}")
    if user_info:
        parts.append("Subject info — " + ", ".join(user_info) + ".")

    if style_name:
        parts.append(f"Target style to apply: {style_name}.")

    if style_features:
        features_text = (
            ", ".join(str(x) for x in style_features if x)
            if isinstance(style_features, list)
            else str(style_features)
        )
        if features_text:
            parts.append(f"Visual features to apply: {features_text}.")

    if target == "hair":
        if not change:
            change = "apply the selected hairstyle naturally"
        parts.append(
            f"EDIT ONLY the hairstyle. Change: {change}. "
            "You may adjust hair length, bangs, parting, volume, curl, and texture. "
            "Do NOT touch makeup, skin, facial structure, expression, outfit, or background."
        )
    elif target == "makeup":
        if not change:
            change = "apply the selected makeup style naturally"
        parts.append(
            f"EDIT ONLY the makeup. Change: {change}. "
            "You may adjust foundation, lip color, blush, eye makeup, contouring, and highlighting. "
            "Do NOT touch hairstyle, facial structure, expression, outfit, or background."
        )
    elif target == "partial":
        if not change:
            change = "apply the requested partial adjustment naturally"
        parts.append(
            f"EDIT ONLY the requested detail. Change: {change}. "
            "Do NOT modify hair, makeup, face shape, outfit, or background."
        )
    else:
        if not change:
            change = "apply natural overall beauty retouching"
        parts.append(
            f"Apply subtle overall beauty retouching. Change: {change}. "
            "Keep the person's identity fully intact. Do not over-retouch."
        )

    parts.append(
        "Hard constraints: preserve face shape, eyes, nose, mouth, expression, pose, and background. "
        "Do not over-smooth skin. Do not alter body shape. "
        "Do not add accessories or decorations not requested. "
        "The result must look like a natural real photograph."
    )

    return " ".join(parts)


def _save_image_to_media(image_data: bytes, mime_type: str) -> str:
    """Save image to MEDIA_ROOT/retouches/ and return the relative URL."""
    ext = "png" if "png" in mime_type else ("webp" if "webp" in mime_type else "jpg")
    filename = f"{uuid.uuid4().hex}.{ext}"
    save_dir = Path(settings.MEDIA_ROOT) / "retouches"
    save_dir.mkdir(parents=True, exist_ok=True)
    (save_dir / filename).write_bytes(image_data)
    return f"{settings.MEDIA_URL}retouches/{filename}"


def _call_gemini_image_edit(payload: dict[str, Any]) -> str:
    """Edit the source image via Gemini and return the saved media URL."""
    source_url = payload["source_image_url"]
    image_bytes, mime_type = _download_image(source_url)
    prompt_text = _build_retouch_prompt(payload)

    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options={"api_version": "v1beta"},
    )

    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    types.Part.from_text(text=prompt_text),
                ],
            )
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            candidate_count=1,
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            result_mime = part.inline_data.mime_type or "image/png"
            return _save_image_to_media(part.inline_data.data, result_mime)

    raise ValueError("Gemini 이미지 응답에서 이미지를 찾을 수 없습니다.")


# ---------------------------------------------------------------------------
# Retouch flow nodes
# ---------------------------------------------------------------------------

def analyze_retouch_request(state: ChatbotState) -> ChatbotState:
    user_message = state.get("user_message", "")
    clarity, request = _analyze_text_request(user_message, state)
    source_image_url = _source_image_url(state)

    pending_retouch = {
        "source_image_url": source_image_url,
        "retouch_request": request,
        "original_user_message": user_message,
    }

    state["retouch_clarity"] = clarity
    state["retouch_request"] = request
    state["pending_retouch"] = pending_retouch
    state["needs_clarification"] = clarity == "ambiguous"
    _set_no_rag(state, "analyze_retouch_request")
    return state


def ask_retouch_clarification(state: ChatbotState) -> ChatbotState:
    user_profile = dict(state.get("user_profile") or {})
    pending_retouch = state.get("pending_retouch") or {
        "source_image_url": _source_image_url(state),
        "retouch_request": state.get("retouch_request"),
        "original_user_message": state.get("user_message", ""),
    }
    user_profile["pending_retouch"] = pending_retouch

    state["user_profile"] = user_profile
    state["answer"] = "어떤 부분을 리터치할까요?"
    state["pending_selection"] = PENDING_RETOUCH_CLARIFICATION
    state["selection"] = {
        "type": PENDING_RETOUCH_CLARIFICATION,
        "options": _CLARIFICATION_OPTIONS,
    }
    state["clarification_options"] = [option["label"] for option in _CLARIFICATION_OPTIONS]
    _set_no_rag(state, "pending_retouch_clarification")
    return state


def handle_retouch_clarification(state: ChatbotState) -> ChatbotState:
    selected_option = state.get("selected_option") or {}
    selected_id = selected_option.get("id")
    user_profile = dict(state.get("user_profile") or {})
    pending_retouch = dict(state.get("pending_retouch") or user_profile.get("pending_retouch") or {})

    if selected_id:
        request = _request_from_option(selected_id, state)
        clarity = "clear"
    else:
        clarity, request = _analyze_text_request(state.get("user_message", ""), state)

    pending_retouch["retouch_request"] = request
    pending_retouch["source_image_url"] = pending_retouch.get("source_image_url") or _source_image_url(state)
    pending_retouch["clarification_response"] = selected_option or state.get("user_message", "")

    state["retouch_request"] = request
    state["retouch_clarity"] = clarity
    state["pending_retouch"] = pending_retouch
    state["pending_selection"] = None
    state["selection"] = None
    state["needs_clarification"] = clarity == "ambiguous"
    user_profile["pending_retouch"] = pending_retouch
    state["user_profile"] = user_profile
    _set_no_rag(state, "handle_retouch_clarification")
    return state


def build_retouch_prompt_payload(state: ChatbotState) -> dict[str, Any]:
    user_profile = state.get("user_profile") or {}
    pending_retouch = state.get("pending_retouch") or user_profile.get("pending_retouch") or {}
    source_image_url = pending_retouch.get("source_image_url") or _source_image_url(state)
    retouch_request = pending_retouch.get("retouch_request") or state.get("retouch_request") or {}

    return {
        "source_image_url": source_image_url,
        "user_profile": {
            "gender": state.get("gender"),
            "face_shape": state.get("face_shape"),
            "face_proportion": state.get("face_proportion"),
            "personal_color": state.get("personal_color"),
            "skin_tone": user_profile.get("skin_tone"),
        },
        "previous_analysis": state.get("previous_analysis"),
        "previous_recommendations": state.get("previous_recommendations") or [],
        "retouch_request": {
            "target": retouch_request.get("target", "overall"),
            "requested_change": retouch_request.get("requested_change", ""),
            "selected_style": retouch_request.get("selected_style"),
        },
        "constraints": [
            "얼굴형, 표정, 눈/코/입 구조는 변경하지 않는다.",
            "피부톤은 과도하게 바꾸지 않는다.",
            "요청한 헤어 또는 메이크업 요소 외에는 최대한 유지한다.",
            "자연스럽고 실제 촬영된 사진처럼 보이게 한다.",
        ],
    }


def ask_retouch_confirmation(state: ChatbotState) -> ChatbotState:
    payload = build_retouch_prompt_payload(state)
    request = payload["retouch_request"]
    target_label = {
        "hair": "헤어",
        "makeup": "메이크업",
        "partial": "부분 보정",
        "overall": "전체 보정",
    }.get(request.get("target"), "전체 보정")

    pending_retouch = dict(state.get("pending_retouch") or {})
    pending_retouch["source_image_url"] = payload.get("source_image_url")
    pending_retouch["retouch_request"] = request
    pending_retouch["prompt_payload"] = payload

    user_profile = dict(state.get("user_profile") or {})
    user_profile["pending_retouch"] = pending_retouch

    state["user_profile"] = user_profile
    state["pending_retouch"] = pending_retouch
    state["retouch_prompt_payload"] = payload
    state["answer"] = (
        "다음 내용으로 리터치를 진행할까요?\n\n"
        f"* 대상: {target_label}\n"
        f"* 수정 내용: {request.get('requested_change') or '요청한 내용 적용'}\n"
        "* 유지 조건: 얼굴형, 표정, 배경은 최대한 유지"
    )
    state["pending_selection"] = PENDING_RETOUCH_CONFIRMATION
    state["selection"] = {
        "type": PENDING_RETOUCH_CONFIRMATION,
        "options": [
            {"id": "confirm_retouch", "label": "리터치 진행하기"},
            {"id": "cancel_retouch", "label": "취소하기"},
        ],
    }
    _set_no_rag(state, "pending_retouch_confirmation")
    return state


def ask_retouch_image_required(state: ChatbotState) -> ChatbotState:
    user_profile = dict(state.get("user_profile") or {})
    pending_retouch = dict(state.get("pending_retouch") or user_profile.get("pending_retouch") or {})
    pending_retouch["source_image_url"] = None
    user_profile["pending_retouch"] = pending_retouch

    state["user_profile"] = user_profile
    state["pending_retouch"] = pending_retouch
    state["answer"] = "리터치를 진행하려면 고객님 사진이 필요해요. 얼굴이 잘 보이는 사진을 업로드해 주세요."
    state["pending_selection"] = PENDING_RETOUCH_IMAGE_REQUIRED
    state["selection"] = None
    _set_no_rag(state, "retouch_image_required")
    return state


def handle_retouch_image_required(state: ChatbotState) -> ChatbotState:
    user_profile = dict(state.get("user_profile") or {})
    pending_retouch = dict(state.get("pending_retouch") or user_profile.get("pending_retouch") or {})
    image_url = state.get("image_url")

    if image_url:
        pending_retouch["source_image_url"] = image_url
        user_profile["pending_retouch"] = pending_retouch
        state["user_profile"] = user_profile
        state["pending_retouch"] = pending_retouch
        state["pending_selection"] = None
        state["selection"] = None
        _set_no_rag(state, "retouch_image_received")
        return state

    state["answer"] = "리터치를 진행하려면 고객님 사진이 필요해요. 얼굴이 잘 보이는 사진을 업로드해 주세요."
    state["pending_selection"] = PENDING_RETOUCH_IMAGE_REQUIRED
    state["selection"] = None
    _set_no_rag(state, "retouch_image_required")
    return state


def handle_retouch_confirmation(state: ChatbotState) -> ChatbotState:
    selected_option = state.get("selected_option") or {}
    selected_id = selected_option.get("id")

    state["pending_selection"] = None
    state["selection"] = None

    if selected_id in {"confirm_retouch", "retouch_yes"}:
        state["retouch_action"] = "confirm"
    else:
        state["retouch_action"] = "cancel"
        clear_pending_retouch(state)
        state["answer"] = "리터치를 취소했습니다. 다른 요청이 있으시면 말씀해 주세요."
        _set_no_rag(state, "retouch_cancelled")

    return state


def run_style_retouch(state: ChatbotState) -> ChatbotState:
    payload = state.get("retouch_prompt_payload") or build_retouch_prompt_payload(state)
    source_image_url = payload.get("source_image_url")

    if not source_image_url:
        return ask_retouch_image_required(state)

    try:
        result_url = _call_gemini_image_edit(payload)
        state["retouch_prompt_payload"] = payload
        state["retouch_result_image_url"] = result_url
        state["retouched_image_url"] = result_url
        state["answer"] = "리터치 결과 이미지를 생성했습니다. 마음에 드시나요?"
        state["retouch_action"] = None
        clear_pending_retouch(state)
        _set_no_rag(state, "retouch_synthesis_complete")
    except Exception as e:
        logger.error("리터치 이미지 생성 실패: %s", e, exc_info=True)
        state["answer"] = "리터치 이미지 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        state["retouch_result_image_url"] = None
        state["retouched_image_url"] = None
        _set_no_rag(state, "retouch_synthesis_error")

    return state


def clear_pending_retouch(state: ChatbotState) -> ChatbotState:
    user_profile = dict(state.get("user_profile") or {})
    user_profile.pop("pending_retouch", None)
    user_profile.pop("pending_retouch_instruction", None)
    state["user_profile"] = user_profile
    state["pending_retouch"] = None
    state["pending_selection"] = None
    state["selection"] = None
    state["retouch_clarity"] = None
    return state


def run_retouch_synthesis(state: ChatbotState) -> ChatbotState:
    return run_style_retouch(state)
