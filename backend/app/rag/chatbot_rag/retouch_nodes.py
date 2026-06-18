from __future__ import annotations

from backend.app.rag.chatbot_rag.intents import PENDING_RETOUCH_CONFIRMATION
from backend.app.rag.chatbot_rag.state import ChatbotState
from backend.app.rag.rag_core.schemas import RetrievalResult


def _empty_retrieval(query: str) -> RetrievalResult:
    return RetrievalResult(
        query=query,
        documents=[],
        retrieved_count=0,
        fallback_stage=None,
        used_filter={},
    )


_EMPTY_INFO: dict = {
    "retrieved_count": 0,
    "fallback_stage": "none",
    "used_filter": {},
    "skipped_rag": True,
}


# ---------------------------------------------------------------------------
# 이미지 편집 LLM stub — 실제 연동 시 이 함수만 교체한다.
# ---------------------------------------------------------------------------

def retouch_with_llm(sim_image_url: str, instruction: str) -> str:
    """
    GAN 합성 이미지를 기반으로 리터칭을 수행한다.

    현재는 stub — 추후 아래 중 하나로 교체:
      - OpenAI GPT-Image-1 edit endpoint
      - Stable Diffusion img2img / inpainting
      - Google Gemini imagen
    반환: 리터칭된 이미지의 URL 또는 경로
    """
    # TODO: 실제 이미지 편집 LLM 연동
    return sim_image_url  # stub: 원본 그대로 반환


# ---------------------------------------------------------------------------
# LangGraph 노드
# ---------------------------------------------------------------------------

def ask_retouch_confirmation(state: ChatbotState) -> ChatbotState:
    """
    리터칭 요청 감지 후 확인 버튼을 제시한다.
    유저의 지시문을 user_profile에 저장해 다음 턴에서 복원한다.
    """
    user_message = state.get("user_message", "")
    user_profile = dict(state.get("user_profile") or {})
    user_profile["pending_retouch_instruction"] = user_message
    state["user_profile"] = user_profile

    state["answer"] = "현재 시뮬레이션 이미지를 리터칭해 드릴까요?"
    state["pending_selection"] = PENDING_RETOUCH_CONFIRMATION
    state["selection"] = {
        "type": PENDING_RETOUCH_CONFIRMATION,
        "options": [
            {"id": "retouch_yes", "label": "네, 리터칭해주세요"},
            {"id": "retouch_no",  "label": "아니요"},
        ],
    }
    state["retrieval_result"] = _empty_retrieval(user_message)
    state["retrieval_info"] = {**_EMPTY_INFO, "skip_reason": "pending_retouch_confirmation"}
    return state


def handle_retouch_confirmation(state: ChatbotState) -> ChatbotState:
    """
    리터칭 확인 버튼 응답을 처리한다.
    - retouch_yes → retouch_action="confirm" → run_retouch_synthesis로 라우팅
    - retouch_no  → retouch_action="cancel"  → 취소 안내 후 update_memory
    """
    selected_option = state.get("selected_option") or {}
    selected_id = selected_option.get("id")
    user_profile = dict(state.get("user_profile") or {})

    state["pending_selection"] = None
    state["selection"] = None

    if selected_id == "retouch_yes":
        instruction = user_profile.pop("pending_retouch_instruction", "")
        state["user_profile"] = user_profile
        state["retouch_instruction"] = instruction
        state["retouch_action"] = "confirm"
    else:
        user_profile.pop("pending_retouch_instruction", None)
        state["user_profile"] = user_profile
        state["retouch_action"] = "cancel"
        state["answer"] = "리터칭을 취소했습니다. 다른 요청이 있으시면 말씀해 주세요."
        state["retrieval_result"] = _empty_retrieval(state.get("user_message", ""))
        state["retrieval_info"] = {**_EMPTY_INFO, "skip_reason": "retouch_cancelled"}

    return state


def run_retouch_synthesis(state: ChatbotState) -> ChatbotState:
    """
    GAN 합성 이미지를 기반으로 리터칭을 수행하고 결과 이미지 URL을 반환한다.
    """
    sim_image_url = state.get("sim_image_url") or ""
    instruction = state.get("retouch_instruction") or ""

    retouched_url = retouch_with_llm(sim_image_url, instruction)

    state["retouched_image_url"] = retouched_url
    state["answer"] = "요청하신 대로 리터칭했습니다. 이미지를 클릭하면 현재 선택 이미지로 적용됩니다."
    state["retouch_action"] = None
    state["retouch_instruction"] = None
    state["pending_selection"] = None
    state["selection"] = None
    state["retrieval_result"] = _empty_retrieval(state.get("user_message", ""))
    state["retrieval_info"] = {**_EMPTY_INFO, "skip_reason": "retouch_synthesis"}
    return state
