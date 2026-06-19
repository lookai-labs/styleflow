from __future__ import annotations

from typing import Any


MAX_CHAT_HISTORY_TURNS = 5
DEFAULT_MAX_HISTORY_MESSAGES = MAX_CHAT_HISTORY_TURNS * 2  # 10 messages = 5 turns


def trim_chat_history(
    chat_history: list[dict[str, str]] | None,
    max_messages: int = DEFAULT_MAX_HISTORY_MESSAGES,
) -> list[dict[str, str]]:
    """
    최근 대화 기록 max_messages개만 유지한다.

    chat_history는 아래 형태를 기준으로 한다.
    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
    ]
    """

    if not chat_history:
        return []

    return list(chat_history)[-max_messages:]


def append_chat_history(
    chat_history: list[dict[str, str]] | None,
    user_message: str,
    assistant_answer: str,
    max_messages: int = DEFAULT_MAX_HISTORY_MESSAGES,
) -> list[dict[str, str]]:
    """
    현재 사용자 메시지와 assistant 답변을 chat_history에 추가한다.
    """

    updated_history = list(chat_history or [])

    if user_message:
        updated_history.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

    if assistant_answer:
        updated_history.append(
            {
                "role": "assistant",
                "content": assistant_answer,
            }
        )

    return trim_chat_history(
        updated_history,
        max_messages=max_messages,
    )


def extract_simple_user_preferences(
    user_message: str,
) -> dict[str, Any]:
    """
    사용자 메시지에서 간단한 취향 정보를 추출한다.

    초기 구현에서는 LLM을 사용하지 않고 keyword 기반으로만 처리한다.
    추후 DB 저장 또는 요약 모델을 붙일 수 있다.
    """

    preferences: dict[str, Any] = {}

    message = user_message.strip()

    if not message:
        return preferences

    if any(keyword in message for keyword in ["손질 오래", "손질 많이", "귀찮", "바빠", "시간 없어"]):
        preferences["prefers_easy_styling"] = True

    if any(keyword in message for keyword in ["짧은 머리", "짧게", "짧은 스타일"]):
        preferences["prefers_short_style"] = True

    if any(keyword in message for keyword in ["긴 머리", "길게", "긴 스타일"]):
        preferences["prefers_long_style"] = True

    if any(keyword in message for keyword in ["앞머리 싫", "이마 보이", "이마 드러"]):
        preferences["prefers_forehead_exposed"] = True

    if any(keyword in message for keyword in ["앞머리 있", "이마 가리", "이마 덮"]):
        preferences["prefers_bangs"] = True

    if any(keyword in message for keyword in ["단정", "깔끔", "회사", "면접", "직장"]):
        preferences["prefers_neat_style"] = True

    if any(keyword in message for keyword in ["힙", "개성", "트렌디", "튀는", "유니크"]):
        preferences["prefers_trendy_style"] = True

    return preferences

def db_rows_to_chat_history(
    rows: list[dict[str, Any]],
    max_turns: int = MAX_CHAT_HISTORY_TURNS,
) -> list[dict[str, str]]:
    """
    DB UserFeedback rows (user_chat + ai_chat) → role/content format.

    rows는 created_at 오름차순(과거→최신)으로 정렬된 상태여야 한다.
    """
    history: list[dict[str, str]] = []
    for row in rows[-max_turns:]:
        user_text = row.get("user_chat") or (row.user_chat if hasattr(row, "user_chat") else None)
        ai_text = row.get("ai_chat") or (row.ai_chat if hasattr(row, "ai_chat") else None)
        if user_text:
            history.append({"role": "user", "content": user_text})
        if ai_text:
            history.append({"role": "assistant", "content": ai_text})
    return history


_LIKE_KEYWORDS = ["좋아", "마음에 들어", "맘에 들어", "예쁘다", "이거 좋아", "선호해"]
_DISLIKE_KEYWORDS = ["싫어", "부담스러워", "과한", "별로", "안 좋아", "아닌 것 같아", "그건 아닌"]
_DIRECTION_MAP = {
    "자연스럽게": "자연스러운 스타일",
    "자연스럽": "자연스러운 스타일",
    "화사하게": "화사한 스타일",
    "깔끔하게": "깔끔한 스타일",
    "부드럽게": "부드러운 스타일",
    "진하게": "진한 표현",
    "밝게": "밝은 느낌",
    "어둡게": "어두운 느낌",
}


def extract_preferences_from_history(
    chat_history: list[dict[str, str]],
) -> dict[str, list[str]]:
    """
    최근 대화에서 유저 취향(좋아요/싫어요/스타일 방향)을 rule 기반으로 추출한다.
    """
    likes: list[str] = []
    dislikes: list[str] = []
    style_direction: list[str] = []

    for msg in chat_history:
        if msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        if any(kw in content for kw in _LIKE_KEYWORDS):
            likes.append(content[:60])
        if any(kw in content for kw in _DISLIKE_KEYWORDS):
            dislikes.append(content[:60])
        for kw, label in _DIRECTION_MAP.items():
            if kw in content and label not in style_direction:
                style_direction.append(label)

    return {
        "likes": likes[-3:],
        "dislikes": dislikes[-3:],
        "style_direction": style_direction[-3:],
    }


def format_recent_turns(
    chat_history: list[dict[str, str]],
    max_turns: int = MAX_CHAT_HISTORY_TURNS,
) -> list[dict[str, str]]:
    """최근 N턴을 role/content 형태로 반환한다."""
    return [
        {"role": msg.get("role", ""), "content": msg.get("content", "")}
        for msg in chat_history[-(max_turns * 2):]
        if msg.get("content", "").strip()
    ]


def extract_style_hints_from_history(
    chat_history: list[dict[str, str]],
) -> str:
    """
    리터치 요청이 모호할 때 이전 대화에서 스타일 방향 힌트를 추출한다.
    예: "자연스럽게"가 이전에 언급됐으면 해당 키워드를 반환.
    """
    found: list[str] = []
    for msg in reversed(chat_history[-6:]):
        if msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        for kw in _DIRECTION_MAP:
            if kw in content and _DIRECTION_MAP[kw] not in found:
                found.append(kw)
        if found:
            break  # 가장 최근 턴에서 찾으면 충분
    return ", ".join(found)


def clear_pending_selection(user_profile: dict[str, Any]) -> dict[str, Any]:
    updated_profile = dict(user_profile)

    updated_profile.pop("pending_selection", None)

    return updated_profile


def merge_user_profile(
    user_profile: dict[str, Any] | None,
    new_preferences: dict[str, Any],
) -> dict[str, Any]:
    """
    기존 user_profile에 새로 추출한 취향 정보를 병합한다.

    같은 key가 있으면 최신 값을 우선한다.
    """

    merged = dict(user_profile)

    for key, value in new_preferences.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value

    return merged