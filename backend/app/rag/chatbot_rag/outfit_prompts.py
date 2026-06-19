from __future__ import annotations

import json
import re
from typing import Any

from backend.app.rag.chatbot_rag.intents import INTENT_OUTFIT_FIT_CHECK

OCCASION_LABELS: dict[str, str] = {
    "interview": "면접",
    "wedding_guest": "결혼식 하객",
    "blind_date": "소개팅/데이트",
    "outing": "나들이/피크닉",
    "office": "출근/오피스",
    "daily": "데일리/캐주얼",
}

_OUTFIT_CONTEXT_LABELS: dict[str, str] = {
    "daily": "데일리룩",
    "date": "데이트룩",
    "wedding_guest": "결혼식 하객룩",
    "office": "출근/면접룩",
    "formal": "격식 있는 자리",
    "casual": "꾸안꾸 캐주얼",
}


def _format_hair(hair: dict[str, Any]) -> str:
    name = hair.get("style_name") or ""
    summary = hair.get("hair_analysis_summary") or hair.get("summary") or ""
    if not name and not summary:
        return "헤어스타일 정보 없음"
    parts = []
    if name:
        parts.append(f"스타일명: {name}")
    if summary:
        parts.append(f"요약: {summary}")
    return "\n".join(parts)


def _format_makeup(makeup: dict[str, Any]) -> str:
    name = makeup.get("style_name") or ""
    summary = makeup.get("makeup_analysis_summary") or makeup.get("summary") or ""
    if not name and not summary:
        return "메이크업 정보 없음"
    parts = []
    if name:
        parts.append(f"스타일명: {name}")
    if summary:
        parts.append(f"요약: {summary}")
    return "\n".join(parts)


def _format_image_analysis(analysis: dict[str, Any] | None) -> str:
    if not analysis:
        return "없음"
    lines = []
    for key, label in [
        ("outfit_type", "의상 종류"),
        ("colors", "색상"),
        ("silhouette", "핏/실루엣"),
        ("formality", "격식도"),
        ("style_mood", "스타일 무드"),
        ("match_points", "어울리는 포인트"),
        ("risk_points", "주의할 포인트"),
    ]:
        val = analysis.get(key)
        if val:
            lines.append(f"- {label}: {val}")
    return "\n".join(lines) if lines else "분석 결과 없음"


def build_outfit_coordination_prompt(
    *,
    gender: str | None,
    face_shape: str | None,
    face_proportion: str | None,
    personal_color: str | None,
    hair_summary: dict[str, Any],
    makeup_summary: dict[str, Any],
    outfit_context: str | None,
    outfit_image_analysis: dict[str, Any] | None,
    outfit_intent: str | None,
    user_message: str,
    previous_analysis: Any = None,
) -> str:
    context_label = _OUTFIT_CONTEXT_LABELS.get(outfit_context or "", outfit_context or "상황 정보 없음")
    is_fit_check = outfit_intent == INTENT_OUTFIT_FIT_CHECK

    if is_fit_check:
        task_description = "사용자가 업로드한 의상 이미지를 분석하고, 현재 추천된 헤어·메이크업과의 조화를 판단하세요."
        output_instruction = """
[출력 형식]
아래 두 섹션을 반드시 포함해서 답변하세요.

[답변]
(한국어 대화형 답변. 의상과 헤어/메이크업 조화에 대해 2~4문장으로 설명하세요.)
[/답변]

[의상후보]
[{"id": "uploaded_outfit", "label": "업로드한 의상", "source": "image"}]
[/의상후보]
""".strip()
    else:
        task_description = f"사용자의 헤어·메이크업 스타일을 바탕으로 '{context_label}' 상황에 어울리는 의상 3가지를 추천하세요."
        output_instruction = """
[출력 형식]
아래 두 섹션을 반드시 포함해서 답변하세요.

[답변]
(한국어 대화형 답변. 추천 의상을 간략히 소개하세요. 2~4문장.)
[/답변]

[의상후보]
[
  {
    "id": "look_1",
    "label": "의상 이름 (간결하게)",
    "description": "이 의상을 추천하는 이유",
    "colors": ["주요 색상1", "주요 색상2"],
    "items": ["아이템1", "아이템2"],
    "avoid": ["피해야 할 것"]
  },
  { "id": "look_2", ... },
  { "id": "look_3", ... }
]
[/의상후보]
""".strip()

    return f"""
당신은 헤어와 메이크업 추천 결과를 바탕으로 의상 코디를 추천하거나 판단하는 AI 어시스턴트입니다.

[역할]
{task_description}

[사용자 진단 정보]
- 성별: {gender or "정보 없음"}
- 얼굴형: {face_shape or "정보 없음"}
- 삼정비율: {face_proportion or "정보 없음"}
- 퍼스널컬러: {personal_color or "정보 없음"}

[추천된 헤어스타일]
{_format_hair(hair_summary)}

[추천된 메이크업]
{_format_makeup(makeup_summary)}

[의상 상황]
{context_label}

[의상 이미지 분석 결과]
{_format_image_analysis(outfit_image_analysis)}

[사용자 질문]
{user_message}

[답변 원칙]
- 존댓말을 사용하세요.
- 인사말, 감탄문, 과한 칭찬은 쓰지 마세요.
- 헤어와 메이크업 스타일과의 연결성을 이유로 설명하세요.
- 피해야 할 아이템도 간략히 언급하세요.
- 내부 식별자(id, code 등)를 답변에 노출하지 마세요.

{output_instruction}
""".strip()


def parse_outfit_response(
    content: str,
    outfit_intent: str | None,
) -> tuple[str, list[dict]]:
    """
    LLM 응답에서 [답변]과 [의상후보] 블록을 파싱한다.
    파싱 실패 시 content 전체를 answer로, 빈 리스트를 outfit_options로 반환한다.
    """
    answer = content
    outfit_options: list[dict] = []

    # 의상후보 블록 추출
    candidate_match = re.search(
        r"\[의상후보\]\s*(.*?)\s*\[/의상후보\]",
        content,
        re.DOTALL,
    )
    if candidate_match:
        raw_json = candidate_match.group(1).strip()
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, list):
                outfit_options = parsed
        except (json.JSONDecodeError, ValueError):
            pass
        # 의상후보 블록을 answer에서 제거
        answer = content[: candidate_match.start()].strip()

    # 답변 블록 추출
    answer_match = re.search(
        r"\[답변\]\s*(.*?)\s*\[/답변\]",
        answer,
        re.DOTALL,
    )
    if answer_match:
        answer = answer_match.group(1).strip()

    # fit_check이고 outfit_options가 비어 있으면 기본값 설정
    if outfit_intent == INTENT_OUTFIT_FIT_CHECK and not outfit_options:
        outfit_options = [{"id": "uploaded_outfit", "label": "업로드한 의상", "source": "image"}]

    return answer, outfit_options


# ---------------------------------------------------------------------------
# 새 outfit_advice 프롬프트 빌더
# ---------------------------------------------------------------------------

def build_outfit_advice_prompt(payload: dict[str, Any]) -> str:
    """
    outfit_advice intent용 LLM 프롬프트.
    이미지 없이도 분석 정보와 선택 스타일 기반으로 의상 추천을 생성한다.
    """
    user_profile = payload.get("user_profile") or {}
    beauty_style = payload.get("current_beauty_style") or {}
    user_request = payload.get("user_request") or {}
    constraints = payload.get("constraints") or []

    source_image_url = payload.get("source_image_url")
    image_line = (
        f"기준 이미지: {source_image_url}" if source_image_url
        else "기준 이미지: 없음 (분석 정보 기반으로 추천)"
    )

    hair = beauty_style.get("selected_hair") or {}
    makeup = beauty_style.get("selected_makeup") or {}
    hair_name = hair.get("style_name", "") if isinstance(hair, dict) else str(hair)
    makeup_name = makeup.get("style_name", "") if isinstance(makeup, dict) else str(makeup)
    retouch_summary = beauty_style.get("latest_retouch_summary") or ""

    occasion = user_request.get("occasion") or ""
    occasion_label = OCCASION_LABELS.get(occasion, occasion or "상황 정보 없음")
    raw_text = user_request.get("raw_text", "")

    personal_color = user_profile.get("personal_color") or "정보 없음"
    gender = user_profile.get("gender") or "정보 없음"
    face_shape = user_profile.get("face_shape") or "정보 없음"

    constraints_str = "\n".join(f"- {c}" for c in constraints) if constraints else ""

    beauty_section = ""
    if hair_name:
        beauty_section += f"- 헤어: {hair_name}\n"
    if makeup_name:
        beauty_section += f"- 메이크업: {makeup_name}\n"
    if retouch_summary:
        beauty_section += f"- 최근 수정 요청: {retouch_summary}\n"
    if not beauty_section:
        beauty_section = "- 현재 스타일 정보 없음\n"

    return f"""당신은 헤어·메이크업 스타일 분석 결과를 바탕으로 상황에 맞는 의상을 추천하는 AI 스타일리스트입니다.

[사용자 진단 정보]
- 성별: {gender}
- 얼굴형: {face_shape}
- 퍼스널컬러: {personal_color}

[현재 뷰티 스타일]
{beauty_section.rstrip()}

[{image_line}]

[추천 상황]
{occasion_label}

[사용자 요청]
{raw_text}

[추천 조건]
{constraints_str}

위 정보를 바탕으로 {occasion_label} 상황에 어울리는 의상 조합을 2~3가지 구체적으로 추천해 주세요.
{personal_color} 퍼스널컬러와 조화되는 색상을 우선으로 하고, 헤어·메이크업 분위기를 해치지 않는 스타일을 제안해 주세요.
존댓말을 사용하고, 인사말·감탄문·과한 칭찬은 쓰지 마세요.
구체적인 아이템 조합(상의 + 하의 + 신발 등)으로 제안하고 색상도 명시해 주세요.
피해야 할 색상이나 스타일도 간략히 언급해 주세요."""


def build_outfit_synthesis_prompt_text(payload: dict[str, Any]) -> str:
    """
    outfit_synthesis용 Gemini 이미지 편집 프롬프트 텍스트.
    """
    user_profile = payload.get("user_profile") or {}
    outfit_request = payload.get("outfit_request") or {}
    preserve = payload.get("preserve") or []

    occasion = outfit_request.get("occasion") or ""
    occasion_label = OCCASION_LABELS.get(occasion, occasion or "상황 정보 없음")
    requested_change = outfit_request.get("requested_change") or outfit_request.get("raw_text", "")
    personal_color = user_profile.get("personal_color") or ""

    preserve_str = "\n".join(f"- {p}" for p in preserve) if preserve else ""

    return f"""제공된 인물 사진을 기준으로 의상만 자연스럽게 변경해 주세요.
요청 상황: {occasion_label}
요청 의상 방향: {requested_change}

얼굴, 헤어스타일, 메이크업, 표정, 포즈, 배경은 유지해 주세요.
의상은 {personal_color} 퍼스널컬러와 조화되게 연출해 주세요.
상황에 맞는 격식과 분위기를 반영해 주세요.
실제 촬영된 자연스러운 인물 사진처럼 보이게 해 주세요.

Only change the outfit.
Preserve face, hairstyle, makeup, expression, pose, and background.
{preserve_str}""".strip()
