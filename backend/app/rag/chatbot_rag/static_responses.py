from __future__ import annotations

from backend.app.rag.chatbot_rag.intents import CATEGORY_HAIR, CATEGORY_MAKEUP

MISSING_ANALYSIS_MESSAGE = (
    "아직 추천 결과가 없어 피드백 상담을 진행하기 어려워요. "
    "먼저 헤어 또는 메이크업 추천 결과를 받은 뒤 다시 질문해 주세요."
)

MISSING_APPLIED_STYLE_MESSAGE = (
    "선택하신 스타일 정보를 찾을 수 없어요. "
    "추천 목록에서 스타일을 다시 선택한 후 상담을 시작해 주세요."
)

CLARIFICATION_OPTIONS = [
    "추천받은 헤어스타일이 나에게 어울리는지 궁금해요.",
    "추천받은 헤어스타일의 손질 방법이 궁금해요.",
    "추천받은 메이크업이 나에게 어울리는지 궁금해요.",
    "추천받은 메이크업의 연출 방법이 궁금해요.",
    "추천 스타일끼리 비교해 보고 싶어요.",
]

HAIR_CLARIFICATION_OPTIONS = [
    "추천받은 헤어스타일이 나에게 어울리는지 궁금해요.",
    "추천받은 헤어스타일의 손질 방법이 궁금해요.",
    "헤어스타일 유지 방법이 궁금해요.",
    "다른 헤어스타일도 추천해 주세요.",
    "추천 헤어스타일끼리 비교해 보고 싶어요.",
]

MAKEUP_CLARIFICATION_OPTIONS = [
    "추천받은 메이크업이 나에게 어울리는지 궁금해요.",
    "추천받은 메이크업의 연출 방법이 궁금해요.",
    "메이크업 오래 유지하는 방법이 궁금해요.",
    "다른 메이크업도 추천해 주세요.",
    "추천 메이크업끼리 비교해 보고 싶어요.",
]

GREETING_MESSAGE = (
    "추천받은 헤어스타일이나 메이크업에 대해 궁금한 점을 물어봐 주세요."
)

SMALLTALK_MESSAGE = (
    "좋아요. 추천 결과에 대해 더 궁금한 점이 있으면 이어서 물어봐 주세요."
)

IRRELEVANT_MESSAGE = (
    "저는 추천받은 헤어스타일과 메이크업에 대한 피드백 상담을 도와드리는 챗봇입니다. "
    "추천 결과의 어울림, 손질·연출 방법, 유지 관리, 스타일 비교에 대해 질문해 주세요."
)

NOISE_MESSAGE = (
    "질문을 이해하기 어려워요. 추천받은 헤어스타일이나 메이크업에 대해 조금 더 구체적으로 입력해 주세요."
)

MISSING_SELECTED_STYLE_MESSAGE = (
    "어떤 스타일에 대한 질문인지 확인할 수 없어요. "
    "추천 목록에서 스타일을 선택한 후 다시 질문해 주세요."
)


def build_clarification_message(category: str | None = None) -> str:
    if category == CATEGORY_MAKEUP:
        options = MAKEUP_CLARIFICATION_OPTIONS
    elif category == CATEGORY_HAIR:
        options = HAIR_CLARIFICATION_OPTIONS
    else:
        options = CLARIFICATION_OPTIONS

    option_lines = [
        f"{index}. {option}"
        for index, option in enumerate(options, start=1)
    ]

    return "\n".join(
        [
            "추천 결과에 대해 어떤 피드백 상담이 필요하신지 조금만 더 알려주세요.",
            "",
            *option_lines,
        ]
    )
