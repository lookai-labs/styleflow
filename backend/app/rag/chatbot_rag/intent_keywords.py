from __future__ import annotations

from backend.app.rag.chatbot_rag.intents import (
    CATEGORY_HAIR,
    CATEGORY_MAKEUP,
    INTENT_COMPARISON,
    INTENT_FOLLOWUP_RECOMMENDATION,
    INTENT_GREETING,
    INTENT_IRRELEVANT,
    INTENT_MAINTENANCE,
    INTENT_MEMORY_RECALL,
    INTENT_MOOD_SELECTION,
    INTENT_NOISE,
    INTENT_OUTFIT_EVENT_COORDINATION,
    INTENT_OUTFIT_FIT_CHECK,
    INTENT_OUTFIT_RECOMMENDATION,
    INTENT_SMALLTALK,
    INTENT_STYLE_RETOUCH,
    INTENT_STYLE_EXPLANATION,
    INTENT_STYLE_FIT,
    INTENT_STYLING_METHOD,
    INTENT_UNCLEAR,
)

from backend.app.rag.chatbot_rag.noise_filter import is_noise

# ---------------------------------------------------------------------------
# mood_selection
# ---------------------------------------------------------------------------
# 분위기/느낌/자연스러운/단정/캐주얼 같은 형용사 단독으로는 mood_selection을
# 반환하지 않는다. 사용자가 "선택을 위임"하거나 "선택지"를 요청할 때만 잡는다.

MOOD_SELECTION_KEYWORDS = [
    "분위기 골라",
    "분위기를 골라",
    "분위기로 골라",
    "무드 골라",
    "무드를 골라",
    "골라줘",
    "선택해줘",
    "선택지",
    "분위기 선택",
    "무드 선택",
    "어떤 분위기로 갈까",
    "어떤 분위기로 갈지",
    "어떤 분위기로 가져가",
    "어떤 무드로",
    "무드로 가져가",
    "분위기로 가져가",
    "메이크업 분위기",
    "메이크업 분위기를 어떻게 잡",
    "분위기를 어떻게 잡",

    # 실제 유저 TPO/무드 표현
    "어떤 느낌",
    "느낌으로",
    "느낌이 좋",
    "느낌으로 가고 싶",
    "꾸미지 않은 느낌",
    "자연스럽고 꾸미지 않은",
    "단정해 보",
    "단정한 느낌",
    "단정한 인상",
    "차분한 느낌",
    "세련된 느낌",
    "깔끔한 느낌",

    # 상황 기반 무드 요청
    "결혼식 가려는데",
    "결혼식 갈 때",
    "결혼식에 맞게",
    "하객으로 가는데",
    "하객룩에 맞게",
    "격식 있는 자리",
    "예식장 갈 때",
    "소개팅에 맞게",
    "데이트에 맞게",
    "면접용으로",
    "면접에 맞게",
]

MOOD_CONTEXT_WORDS = [
    "분위기",
    "무드",
    "느낌",
    "이미지",
]

MOOD_DELEGATE_WORDS = [
    "골라",
    "선택해줘",
    "추천해줘",
    "정해줘",
    "가져가면 좋",
    "갈까",
    "갈지",
]

# mood_selection으로 오인하기 쉬운 표현. 이 표현이 있으면 styling_method/fit이 담당한다.
MOOD_FALSE_POSITIVE_PHRASES = [
    "분위기 있게",
    "선택 기준",
    "색조를 처음",
    "실수가 적은",
    "자연스러운 쉐이딩",
    "완성된 느낌",
    "이미지로 통일",
]

# ---------------------------------------------------------------------------
# 우선순위 구문 — 키워드 루프보다 먼저 검사한다.
# ---------------------------------------------------------------------------

STYLE_FIT_PRIORITY_PHRASES = [
    "출근할 때도 괜찮",
    "출근할 때 괜찮",
    "데일리로 하기 괜찮",
    "데일리로 괜찮",
    "이 스타일 괜찮",
    "스타일인가요",
    "현실적",
    "데이트할 때",
    "면접용으로도",
    "좋은 인상",
    "어른스러운 방향",
    "아저씨처럼 보",
    "학생처럼 보",
    "촌스럽",
    "창백해 보",
]

# ---------------------------------------------------------------------------
# intent 키워드 테이블
#
# 루프 우선순위:
#   comparison → maintenance → styling_method → mood_selection → style_fit
# ---------------------------------------------------------------------------

INTENT_KEYWORDS: dict[str, list[str]] = {
    INTENT_COMPARISON: [
        "비교",
        "둘 중",
        " vs ",
    ],
    INTENT_MAINTENANCE: [
        "유지",
        "관리",
        "주기",
        "얼마나",
        "오래",
        "손 많이",
        "수정화장",
        "무너짐",
        "무너질",
        "무너지",
        "자라면",
        "자랐을 때",
        "뿌리가 자란",
        "지속",
        "비용",
        "망가지",
        "망가짐",
        "흐트러",
        "눌려",
        "눌림",
        "눌리",
        "버텨줄",
        "버틸",
        "물놀이",
        "비를 자주",
        "헬멧",
        "모자",
        "위생 모자",
        "귀마개",
        "바람",
    ],
    INTENT_STYLING_METHOD: [
        "손질",
        "드라이",
        "고데기",
        "왁스",
        "스프레이",
        "세팅",
        "스타일링",
        "말리",
        "바르는",
        "바르면",
        "립",
        "립 라이너",
        "블러셔",
        "섀도우",
        "쉐도우",
        "아이섀도우",
        "언더라인",
        "아이라인",
        "눈썹",
        "베이스",
        "제형",
        "컨투어링",
        "쉐이딩",
        "하이라이터",
        "연출",
        "화장법",
        "메이크업법",
        "사진",
        "또렷",
        "어떻게 해야",
        "어떻게 하면",
        "어떻게 해",
        "어떻게 눌",
        "눌러줘",
        "방법",
        "방향",
        "포인트",
        "어디에 포인트",
        "볼륨",
        "어디에 넣",
        "어디에 볼륨",
        "정수리 볼륨",
        "옆 볼륨",
        "피부 표현",
        "피부가 더 좋아 보",
        "매트",
        "촉촉",
        "진하게",
        "연하게",
        "다듬어",
        "조정",
        "피해야",
        "피해서",
        "처리",
        "살리",
        "바꾸려면",
        "바꿔야",
        "어떻게 잡",
        "정리해야",
        "어떻게 다듬",
        "줄여야",
        "줄이면",
        "보완",
        "달라질",
        "그리면",
        "고려해야",
        "고정되는 방법",
        "밝은 곳에서",
        "조명",
        "화상통화",
        "줌",
        "쌩얼에 가깝게",
        "완성된 느낌",
        "하나의 이미지로 통일",
        "이미지로 통일",
        "파악",
        "위치",
        "컬의 위치",
        "입문자",
        "실수",
        "실수가 적은",
        "빠르게 완성",
        "중요한 자리",
        "조합",
        "덜 자르게",
        "디자이너에게",
        "예약 시",
        "선호도",
        "전달하는 게",
        "선택 기준",
        "처음 써보",
        "컬러가 뭐야",
    ],
    INTENT_MOOD_SELECTION: MOOD_SELECTION_KEYWORDS,
    INTENT_STYLE_FIT: [
        "어울",
        "괜찮",
        "맞아",
        "어때",
        "나한테",
        "잘 맞",
        "퍼스널컬러",
        "쿨톤",
        "웜톤",
        "봄웜",
        "여름쿨",
        "가을웜",
        "겨울쿨",
        "코랄",
        "로즈",
        "피치",
        "레드",
        "브라운",
        "추천받은",
        "세련",
        "깔끔",
        "부드러운",
        "부드럽",
        "차분",
        "어려 보",
        "성숙",
        "튀는 건 싫",
        "바꾸고 싶",
        "달라지고 싶",
        "짧은 머리",
        "기장",
        "앞머리",
        "이마",
        "얼굴이 길어",
        "길어 보",
        "둥글어 보",
        "얼굴형",
        "볼살",
        "칙칙",
        "화려하지",
        "부담",
        "고민",
        "데일리",
        "어울릴까",
        "맞을까",
        "괜찮을까",
        "부담스럽지",
        "자연스러워",
        "변한 느낌",
        "답답해 보",
        "면접용",
        "목이 짧",
        "눈이 작은",
        "직종",
        "어른스러운",
        "아저씨처럼",
        "학생처럼",
        "촌스럽",
        "창백해 보",
        "좋은 인상",
    ],
}

MAKEUP_CATEGORY_KEYWORDS = [
    "메이크업",
    "화장",
    "색조",
    "립",
    "립 라이너",
    "입술",
    "블러셔",
    "치크",
    "섀도우",
    "쉐도우",
    "아이섀도우",
    "아이 메이크업",
    "언더라인",
    "아이라인",
    "눈썹",
    "눈매",
    "베이스",
    "피부 표현",
    "피부",
    "제형",
    "톤업",
    "하이라이터",
    "쉐이딩",
    "컨투어링",
    "퍼스널컬러",
    "봄웜",
    "여름쿨",
    "가을웜",
    "겨울쿨",
    "피치",
    "코랄",
    "주시",
    "쥬시",
    "듀이",
    "내추럴",
    "로즈",
    "브라운",
    "시크",
    "오피스",
    "버건디",
    "글램",
    "레드",
]

HAIR_CATEGORY_KEYWORDS = [
    "헤어",
    "머리",
    "스타일",
    "커트",
    "펌",
    "앞머리",
    "옆머리",
    "정수리",
    "두상",
    "기장",
    "컬",
    "볼륨",
    "드라이",
    "왁스",
    "스프레이",
    "디자이너",
    "미용실",
]

AMBIGUOUS_MESSAGES: set[str] = {
    "이거",
    "그거",
    "추천해줘",
    "어떻게 해",
    "어떻게 하면 돼",
    "뭐가 좋아",
    "괜찮아",
    "별로야",
    "좋아",
}

GREETING_KEYWORDS = [
    "안녕",
    "안녕하세요",
    "하이",
    "hello",
    "hi",
    "반가워",
    "반갑습니다",
    "처음이야",
    "처음 뵙겠습니다",
]

SMALLTALK_KEYWORDS = [
    "고마워",
    "감사",
    "좋아",
    "알겠어",
    "오케이",
    "ㅇㅋ",
    "네",
    "응",
]

IRRELEVANT_KEYWORDS = [
    "날씨",
    "주식",
    "코딩",
    "파이썬",
    "게임",
    "여행",
    "음식",
    "맛집",
    "뉴스",
    "정치",
    "영화",
    "노래",
]

# ---------------------------------------------------------------------------
# outfit 키워드 — 명시적으로 의상/옷/코디가 언급된 경우에만 outfit intent로 분류한다.
# ---------------------------------------------------------------------------

OUTFIT_EXPLICIT_KEYWORDS = [
    "의상",
    "옷",
    "코디",
    "입을",
    "뭐 입",
    "어떤 옷",
    "어떤 의상",
    "패션",
    "착장",
    "하객룩",
    "데이트룩",
    "오피스룩",
    "데일리룩",
    "룩 추천",
    "코디 추천",
    "아우터",
]

OUTFIT_FIT_CHECK_PHRASES = [
    "이 의상",
    "이 옷",
    "이 코디",
    "이 룩",
]

# ---------------------------------------------------------------------------
# style_explanation — 선택된 스타일에 대한 설명/정의 질문 감지
#
# 지시어(이거/이건/이 메이크업/이 스타일 등) + 설명 요청어의 조합으로 판별한다.
# mood_selection보다 먼저 검사해 "이 메이크업은 어떤 느낌이야?" 같은 오탐을 방지한다.
# ---------------------------------------------------------------------------

STYLE_EXPLANATION_POINTING_WORDS = [
    "이거",
    "이건",
    "이게",
    "이걸",
    "이 메이크업",
    "이 화장",
    "이 스타일",
    "이 머리",
    "이 헤어스타일",
    "이 헤어",
]

STYLE_EXPLANATION_DESCRIPTION_WORDS = [
    "뭐야",
    "뭔가요",
    "뭐예요",
    "무슨 메이크업",
    "무슨 스타일",
    "무슨 헤어",
    "무슨 머리",
    "어떤 메이크업",
    "어떤 스타일",
    "어떤 헤어",
    "어떤 머리",
    "설명해",
    "특징",
    "어떤 느낌이야",
    "어떤 느낌인",
    "어떤 느낌이에요",
    "어떤 분위기야",
    "어떤 분위기인",
    "어떤 분위기예요",
    "어떤 거야",
    "어떤 건지",
    "어떤 스타일인지",
    "어떤 메이크업인지",
]

OUTFIT_EVENT_KEYWORDS = [
    "결혼식",
    "하객",
    "면접",
    "데이트",
    "소개팅",
    "출근",
    "격식",
    "예식",
    "행사",
]

# ---------------------------------------------------------------------------
# retouch — GAN 합성 이미지 직접 편집 요청 감지
# ---------------------------------------------------------------------------

# 이미지를 명시적으로 지칭하는 표현
RETOUCH_EXPLICIT_KEYWORDS = [
    "리터치",
    "리터치해줘",
    "리터칭",
    "보정해줘",
    "보정해 줘",
    "적용해줘",
    "적용해 줘",
    "합성해줘",
    "합성해 줘",
    "예쁘게 바꿔줘",
    "예쁘게 바꿔 줘",
    "좀 수정해줘",
    "좀 수정해 줘",
    "메이크업 바꿔줘",
    "메이크업 바꿔 줘",
    "머리 바꿔줘",
    "머리 바꿔 줘",
    "자연스럽게 해줘",
    "자연스럽게 해 줘",
    "이 이미지",
    "이 사진",
    "이 합성",
    "합성 이미지",
    "시뮬레이션 이미지",
    "시뮬레이션 사진",
    "이미지를 바꿔",
    "이미지 바꿔",
    "사진을 바꿔",
    "사진 바꿔",
    "이미지 수정",
    "사진 수정",
    # 욕구형 표현 — "수정하고 싶어" 등
    "수정하고 싶어",
    "수정하고 싶",
    "바꾸고 싶어",
    "바꾸고 싶",
    "고치고 싶어",
    "고치고 싶",
    "조정하고 싶어",
    "조정하고 싶",
    "보정하고 싶어",
    "보정하고 싶",
    "적용하고 싶어",
    "합성하고 싶어",
]

# 직접 수정 요청 동사
RETOUCH_EDIT_VERBS = [
    "바꿔줘",
    "바꿔 줘",
    "수정해줘",
    "수정해 줘",
    "변경해줘",
    "변경해 줘",
    "고쳐줘",
    "고쳐 줘",
    "적용해줘",
    "적용해 줘",
    "합성해줘",
    "합성해 줘",
    "보정해줘",
    "보정해 줘",
]

RETOUCH_STYLE_TARGET_PHRASES = [
    "이 헤어로 바꿔",
    "이 메이크업으로 바꿔",
    "앞머리만 바꿔",
    "립을 더 진하게",
    "립 더 진하게",
    "피부톤을 자연스럽게",
    "피부톤 자연스럽게",
    "선택한",
    "추천받은",
    "추천된",
]

# 이미지/사진 또는 뷰티 부위 명사 (동사와 조합 시 retouch로 판별)
RETOUCH_IMAGE_NOUNS = [
    "이미지",
    "사진",
    "합성",
    "시뮬레이션",
    # 뷰티 부위 명사
    "헤어",
    "머리",
    "앞머리",
    "메이크업",
    "화장",
    "립",
    "눈",
    "피부톤",
]


# ---------------------------------------------------------------------------
# 자연어 리터치 감지 — 부위 키워드 + 변화 표현 조합
# ---------------------------------------------------------------------------

MAKEUP_PART_KEYWORDS = [
    "입술", "립", "아이라인", "눈매", "눈썹",
    "볼", "치크", "블러셔", "피부톤",
    "섀도우", "쉐도우", "아이섀도우",
    "하이라이터", "쉐이딩", "컨투어링",
]

HAIR_PART_KEYWORDS = [
    "앞머리", "옆머리", "뒷머리",
    "컬", "웨이브", "볼륨",
    "기장", "두상", "정수리", "뿌리",
]

CHANGE_KEYWORDS = [
    "만들고 싶어", "만들어 줘", "만들어줘",
    "하고 싶어", "해줘", "해 줘",
    "변경하고 싶어", "변경해줘", "변경해 줘",
    "내리고 싶어", "올리고 싶어",
    "길게 하고 싶어", "짧게 하고 싶어",
    "진하게", "연하게", "밝게", "어둡게",
    "자연스럽게", "강하게", "부드럽게",
    "빨갛게", "핑크색으로", "갈색으로", "검은색으로",
    "더 자연스럽게", "더 진하게", "더 연하게",
]

# 충돌 감지용 부위 키워드 (반대 카테고리 명시 부위)
_MAKEUP_CONFLICT_PARTS = [
    "입술", "립", "아이라인", "눈매", "눈썹",
    "볼", "치크", "블러셔",
    "섀도우", "쉐도우", "아이섀도우",
    "하이라이터", "쉐이딩", "컨투어링",
    "피부톤",
]

_HAIR_CONFLICT_PARTS = [
    "앞머리", "옆머리", "뒷머리",
    "컬", "웨이브",
    "두상", "정수리", "뿌리",
]


def detect_natural_retouch_target(message: str) -> str | None:
    """
    (뷰티 부위 키워드) + (변화 표현) 조합이면 자연어 리터치 요청으로 판별한다.
    반환: CATEGORY_MAKEUP | CATEGORY_HAIR | None
    """
    msg = message.strip().lower()
    if not any(kw in msg for kw in CHANGE_KEYWORDS):
        return None
    if any(kw in msg for kw in MAKEUP_PART_KEYWORDS):
        return CATEGORY_MAKEUP
    if any(kw in msg for kw in HAIR_PART_KEYWORDS):
        return CATEGORY_HAIR
    return None


def detect_category_conflict(message: str, target_type: str | None) -> bool:
    """
    target_type이 고정된 채팅방에서 반대 카테고리 신체 부위가 언급되면 True.
    """
    if not target_type:
        return False
    msg = message.strip().lower()
    if target_type == CATEGORY_HAIR:
        return any(kw in msg for kw in _MAKEUP_CONFLICT_PARTS)
    if target_type == CATEGORY_MAKEUP:
        return any(kw in msg for kw in _HAIR_CONFLICT_PARTS)
    return False


_MEMORY_RECALL_PHRASES = [
    "방금 뭐라고 했지",
    "방금 뭐라고 했어",
    "아까 내가 뭐라고",
    "내가 방금 뭐라고",
    "방금 한 말",
    "아까 한 말",
    "내가 직전에 뭐라고",
    "전에 뭐라고 했지",
    "방금 말한 게",
    "방금 말한 거",
    "방금 한 게",
]


def is_memory_recall(message: str) -> bool:
    msg = message.strip().lower()
    return any(phrase in msg for phrase in _MEMORY_RECALL_PHRASES)


_FOLLOWUP_RECOMMENDATION_PHRASES = [
    "다른 메이크업",
    "다른 헤어",
    "다른 스타일",
    "다른 건",
    "다른 거",
    "다른 것도",
    "또 뭐 있어",
    "또 추천",
    "다른 추천",
    "다른 것도 추천",
    "그럼 다른",
    "또 다른",
]


def is_followup_recommendation(message: str) -> bool:
    msg = message.strip().lower()
    return any(phrase in msg for phrase in _FOLLOWUP_RECOMMENDATION_PHRASES)


def is_retouch_request(message: str) -> bool:
    """
    GAN 합성 이미지에 대한 직접 편집/수정 요청인지 판별한다.
    classify_intent 노드에서 sim_image_url 존재 여부와 함께 확인한다.
    """
    msg = message.strip().lower()
    if any(kw in msg for kw in RETOUCH_EXPLICIT_KEYWORDS):
        return True
    if any(phrase in msg for phrase in RETOUCH_STYLE_TARGET_PHRASES):
        return any(v in msg for v in RETOUCH_EDIT_VERBS) or any(v in msg for v in ["해줘", "해 줘"])
    has_verb = any(v in msg for v in RETOUCH_EDIT_VERBS)
    has_noun = any(n in msg for n in RETOUCH_IMAGE_NOUNS)
    return has_verb and has_noun


_GREETING_STRIP_CHARS = "!?~ㅎㅋ\t\n "
_GREETING_SET = {kw.lower() for kw in GREETING_KEYWORDS}


def _has_any(message: str, phrases: list[str]) -> bool:
    return any(phrase.lower() in message for phrase in phrases)


def _is_pure_greeting(message: str) -> bool:
    """메시지 전체가 인사 표현일 때만 True를 반환한다."""
    stripped = message.strip(_GREETING_STRIP_CHARS).lower()
    return stripped in _GREETING_SET


def _is_style_explanation_request(message: str) -> bool:
    """
    지시어(이거/이건/이 메이크업/이 스타일) + 설명 요청어 조합이면 True.

    mood_selection보다 먼저 검사해 "이 메이크업은 어떤 느낌이야?" 같은 표현이
    mood_selection으로 오분류되는 것을 막는다.
    """
    has_pointing = _has_any(message, STYLE_EXPLANATION_POINTING_WORDS)
    if not has_pointing:
        return False
    return _has_any(message, STYLE_EXPLANATION_DESCRIPTION_WORDS)


def _is_mood_selection_request(message: str) -> bool:
    """
    mood_selection은 선택 위임 의도가 명확할 때만 True.

    "선택 기준"처럼 방법을 묻는 표현은 제외한다.
    """
    if _has_any(message, MOOD_FALSE_POSITIVE_PHRASES):
        return False

    if _has_any(message, MOOD_SELECTION_KEYWORDS):
        return True

    has_context = _has_any(message, MOOD_CONTEXT_WORDS)
    has_delegate = _has_any(message, MOOD_DELEGATE_WORDS)
    return has_context and has_delegate


def _is_outfit_request(message: str) -> bool:
    return _has_any(message, OUTFIT_EXPLICIT_KEYWORDS)


def _get_outfit_intent(message: str) -> str:
    if _has_any(message, OUTFIT_FIT_CHECK_PHRASES):
        return INTENT_OUTFIT_FIT_CHECK
    if _has_any(message, OUTFIT_EVENT_KEYWORDS):
        return INTENT_OUTFIT_EVENT_COORDINATION
    return INTENT_OUTFIT_RECOMMENDATION


def _has_explicit_comparison(message: str) -> bool:
    """
    2개 항목을 명확하게 비교하는 구조일 때만 True를 반환한다.
    단순히 "제일", "가장", "어떤 게", "뭐가 좋아"만으로는 비교 처리하지 않는다.
    """
    if "둘 중" in message:
        return True

    if " vs " in message.lower():
        return True

    if message.count("나을까") >= 2:
        return True

    if "어느 쪽" in message:
        return True

    if any(phrase in message for phrase in ["더 맞는 건", "더 쉬운 건", "더 나은 건"]):
        return True

    if "랑" in message and any(p in message for p in ["중에서", "중 ", "뭐가 더", "어느 쪽"]):
        return True

    if "와" in message and any(p in message for p in ["중에서", "중 ", "뭐가 더", "어느 쪽"]):
        return True

    if "과" in message and any(p in message for p in ["중에서", "중 ", "뭐가 더", "어느 쪽"]):
        return True

    if "중" in message and "뭐가 더" in message:
        return True

    return False


def get_intent_by_keyword(message: str) -> str:
    if is_noise(message):
        return INTENT_NOISE

    normalized_message = message.strip().lower()

    if any(keyword in normalized_message for keyword in IRRELEVANT_KEYWORDS):
        return INTENT_IRRELEVANT

    if _is_pure_greeting(normalized_message):
        return INTENT_GREETING

    if normalized_message in SMALLTALK_KEYWORDS:
        return INTENT_SMALLTALK

    # 대화 기억 질문 — 다른 intent보다 우선
    if is_memory_recall(normalized_message):
        return INTENT_MEMORY_RECALL

    # 명확한 비교 구조는 maintenance/styling 키워드보다 우선한다.
    if _has_explicit_comparison(normalized_message):
        return INTENT_COMPARISON

    if is_retouch_request(normalized_message):
        return INTENT_STYLE_RETOUCH

    # 후속 추천 질문
    if is_followup_recommendation(normalized_message):
        return INTENT_FOLLOWUP_RECOMMENDATION

    # outfit 키워드가 명시적으로 있으면 mood_selection보다 먼저 잡는다.
    if _is_outfit_request(normalized_message):
        return _get_outfit_intent(normalized_message)

    # 지시어 + 설명 요청어 조합은 mood_selection보다 먼저 잡는다.
    # "이 메이크업은 어떤 느낌이야?" 같은 표현이 mood_selection으로 오분류되는 것을 방지.
    if _is_style_explanation_request(normalized_message):
        return INTENT_STYLE_EXPLANATION

    # mood_selection은 선택 위임 의도가 명확할 때만 허용한다.
    if _is_mood_selection_request(normalized_message):
        return INTENT_MOOD_SELECTION

    # style_fit 우선 구문 — 일부 표현은 styling_method 단어와 섞여도 적합성 판단이 핵심이다.
    if _has_any(normalized_message, STYLE_FIT_PRIORITY_PHRASES):
        return INTENT_STYLE_FIT

    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword.lower() in normalized_message for keyword in keywords):
            return intent

    if normalized_message in AMBIGUOUS_MESSAGES:
        return INTENT_UNCLEAR

    return INTENT_UNCLEAR


def _extract_outfit_context_from_message(user_message: str) -> str | None:
    """사용자 메시지에서 의상 상황 id를 추출한다."""
    msg = user_message.lower()
    if any(k in msg for k in ["결혼식", "하객", "예식"]):
        return "wedding_guest"
    if any(k in msg for k in ["데이트", "소개팅"]):
        return "date"
    if any(k in msg for k in ["면접", "출근", "오피스"]):
        return "office"
    if any(k in msg for k in ["격식", "공식 행사", "공식 자리"]):
        return "formal"
    if "캐주얼" in msg or "꾸안꾸" in msg:
        return "casual"
    if "데일리" in msg:
        return "daily"
    return None


def detect_question_category(message: str) -> str:
    normalized_message = message.strip().lower()

    if any(keyword.lower() in normalized_message for keyword in MAKEUP_CATEGORY_KEYWORDS):
        return CATEGORY_MAKEUP

    if any(keyword.lower() in normalized_message for keyword in HAIR_CATEGORY_KEYWORDS):
        return CATEGORY_HAIR

    return CATEGORY_HAIR
