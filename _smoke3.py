import sys
sys.path.insert(0, '.')
from backend.app.rag.chatbot_rag.intent_keywords import is_recommendation_recall

# No-space variants that failed before the fix
nospace_cases = [
    ("내가 추천받은게 뭐야?", True),       # "받은게" = "받은 게"
    ("추천받은거 다시 알려줘", True),        # "받은거" = "받은 거"
    ("나한테 추천된게 뭐였지?", True),       # "된게" = "된 게"
    ("지금 선택한게 뭐야?", True),          # close enough? let's see
    ("내 추천결과 알려줘", True),           # "추천결과" = "추천 결과"
]
# Original spaced variants (should still work)
spaced_cases = [
    ("내가 추천받은 게 뭐야?", True),
    ("추천받은 거 다시 알려줘", True),
    ("내가 추천받은 스타일이 뭐야?", True),
    ("추천 결과 알려줘", True),
    ("이 스타일 나한테 어울려?", False),
    ("다른 헤어스타일도 추천해줘", False),
]

all_ok = True
print("=== No-space variants ===")
for msg, expected in nospace_cases:
    result = is_recommendation_recall(msg)
    ok = result == expected
    if not ok:
        all_ok = False
    print(f"  [{'OK' if ok else 'FAIL'}] \"{msg}\" -> {result}")

print()
print("=== Original spaced variants ===")
for msg, expected in spaced_cases:
    result = is_recommendation_recall(msg)
    ok = result == expected
    if not ok:
        all_ok = False
    print(f"  [{'OK' if ok else 'FAIL'}] \"{msg}\" -> {result}")

print()
print("ALL OK" if all_ok else "SOME TESTS FAILED")
sys.exit(0 if all_ok else 1)
