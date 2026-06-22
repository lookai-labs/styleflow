"""diagnose.py 분석 결과 → hair.md / makeup.xlsx 기반 헤어스타일·메이크업 추천.

diagnose.py가 반환한 얼굴형/삼정/퍼스널컬러 결과를 hair.md(헤어스타일 매핑 표),
makeup.xlsx(퍼스널컬러별 메이크업 표)와 매칭해 추천 결과 dict를 만든다.
이 모듈은 추천 결과를 만드는 데까지만 책임지며, DB 적재는 호출하는 쪽에서 처리한다.

diagnose.py의 face_shape["label"]은 shape_classification.py의 _KO 매핑을 거쳐
이미 hair.md와 동일한 한글 표기(계란형/둥근형/각진형/장방형/역삼각형)로 나오므로
별도 영→한 매핑 없이 바로 사용한다.

사용법
------
    python Recommend.py 사진.jpg --gender female
    python Recommend.py 사진.jpg --gender male --json
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

_ROOT        = Path(__file__).parent
_HAIR_MD     = _ROOT / "hair.md"
_MAKEUP_XLSX = _ROOT / "makeup.xlsx"

# 사용자 성별(male/female) → hair.md 성별 표기
GENDER_EN_TO_KO = {"male": "남성", "female": "여성"}
GENDER_TO_MAKEUP_LABEL = {"male": "남", "female": "여"}

# personal_color 라벨(skin/config.py CLASS_DISPLAY_NAMES 키) → makeup.xlsx 퍼스널 컬러 표기
PERSONAL_COLOR_TO_MAKEUP_LABEL = {
    "spring_warm": "봄 웜",
    "summer_cool": "여름 쿨",
    "autumn_warm": "가을 웜",
    "winter_cool": "겨울 쿨",
}

SAMJEONG_PARTS = ["상안부", "중안부", "하안부"]


# ─── hair.md 파싱 ────────────────────────────────────────────────────────────

_hair_table_cache: Optional[list[dict]] = None


def _split_items(cell: str) -> list[str]:
    cell = cell.strip()
    if cell in ("", "-"):
        return []
    return [x.strip() for x in cell.split(",") if x.strip()]


def _load_hair_table(path: Path = _HAIR_MD) -> list[dict]:
    """hair.md의 마크다운 표를 행 dict 리스트로 파싱 (결과 캐시됨)."""
    global _hair_table_cache
    if _hair_table_cache is not None:
        return _hair_table_cache

    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 7 or cells[0] not in ("남성", "여성"):
            continue  # 헤더/구분선/그 외 텍스트 스킵
        rows.append({
            "gender":        cells[0],
            "face_shape":    cells[1],
            "samjeong":      cells[2],
            "expert":        _split_items(cells[3]),
            "crawled":       _split_items(cells[4]),
            "supplement":    _split_items(cells[5]),
            "not_recommend": _split_items(cells[6]),
        })

    _hair_table_cache = rows
    return rows


def _samjeong_to_hair_label(samjeong: Optional[dict]) -> str:
    """diagnose.py의 samjeong 결과 → hair.md 삼정비율 표기('균형'|'상안부 발달'|...).

    상·중안부 두 곳이 동시에 긴 경계형(long_parts 2개)은 hair.md에 해당 칸이 없어
    가장 긴 한 곳만으로 근사 매칭한다.
    """
    if not samjeong or samjeong.get("is_balanced", True):
        return "균형"

    long_parts = samjeong.get("long_parts") or [samjeong.get("longest")]
    part = long_parts[0]
    if part not in SAMJEONG_PARTS:
        return "균형"
    return f"{part} 발달"


def recommend_hairstyle(face_shape_label: str, samjeong: Optional[dict], gender: str) -> dict:
    """
    얼굴형(한글 라벨) + 삼정 결과 + 성별("male"|"female") → hair.md 추천 헤어스타일.

    Returns
    -------
    {
        "matched": bool,
        "gender": str, "face_shape": str, "samjeong": str,
        "recommended": [...],       # 전문가 추천 + 크롤링 데이터 + 보완 추가 (중복 제거, 순서 유지)
        "not_recommended": [...],
    }
    """
    gender_ko = GENDER_EN_TO_KO.get(gender, gender)
    samjeong_label = _samjeong_to_hair_label(samjeong)

    for row in _load_hair_table():
        if row["gender"] == gender_ko and row["face_shape"] == face_shape_label and row["samjeong"] == samjeong_label:
            recommended: list[str] = []
            for items in (row["expert"], row["crawled"], row["supplement"]):
                for item in items:
                    if item not in recommended:
                        recommended.append(item)
            return {
                "matched":         True,
                "gender":          gender_ko,
                "face_shape":      face_shape_label,
                "samjeong":        samjeong_label,
                "recommended":     recommended,
                "not_recommended": row["not_recommend"],
            }

    return {
        "matched":         False,
        "gender":          gender_ko,
        "face_shape":      face_shape_label,
        "samjeong":        samjeong_label,
        "recommended":     [],
        "not_recommended": [],
    }


# ─── makeup.xlsx 파싱 ────────────────────────────────────────────────────────

_makeup_table_cache: Optional[dict] = None


def _load_makeup_table(path: Path = _MAKEUP_XLSX) -> dict:
    """makeup.xlsx → {(성별, 퍼스널 컬러): [메이크업, ...]} (결과 캐시됨)."""
    global _makeup_table_cache
    if _makeup_table_cache is not None:
        return _makeup_table_cache

    df = pd.read_excel(path, sheet_name=0)

    table: dict = {}
    for _, row in df.iterrows():
        gender = str(row["성별"]).strip()
        personal_color = str(row["퍼스널 컬러"]).strip()
        makeup = row["메이크업"]
        if not isinstance(makeup, str):
            continue
        key = (gender, personal_color)
        table.setdefault(key, []).append(makeup.strip())

    _makeup_table_cache = table
    return table


def recommend_makeup(personal_color: dict, gender: str = "female") -> dict:
    """
    diagnose.py의 personal_color 결과 + 성별 → makeup.xlsx 추천 메이크업.
    output_type == "boundary_top2"면 top1/top2 두 컬러의 메이크업을 모두 합쳐 제공한다.

    Returns
    -------
    {"matched": bool, "labels": [...], "recommended": [...]}
    """
    if not personal_color or personal_color.get("error"):
        return {"matched": False, "labels": [], "recommended": []}

    if personal_color.get("output_type") == "boundary_top2":
        candidate_labels = personal_color.get("candidates", [])
    else:
        candidate_labels = [personal_color.get("final_label")]

    gender_label = GENDER_TO_MAKEUP_LABEL.get(gender, "여")
    table = _load_makeup_table()
    labels: list[str] = []
    recommended: list[str] = []
    for label in candidate_labels:
        makeup_label = PERSONAL_COLOR_TO_MAKEUP_LABEL.get(label)
        if makeup_label is None:
            continue
        labels.append(makeup_label)
        for item in table.get((gender_label, makeup_label), []):
            if item not in recommended:
                recommended.append(item)

    return {"matched": bool(recommended), "labels": labels, "recommended": recommended}


# ─── 통합 추천 ───────────────────────────────────────────────────────────────

def recommend(diagnosis: dict, gender: str) -> dict:
    """
    diagnose.py의 diagnose() 결과 + 성별 → 헤어스타일/메이크업 추천 통합 결과.

    DB 적재 직전까지의 결과(dict)를 반환한다. 실제 DB 저장은 호출하는 쪽의 책임.

    Returns
    -------
    {
        "image_path": str, "gender": str,
        "hairstyle": dict | None,
        "makeup":    dict,
        "warnings":  list[str],
    }
    """
    warnings: list[str] = list(diagnosis.get("warnings", []))

    face_shape = diagnosis.get("face_shape")
    hairstyle = None
    if face_shape is None:
        warnings.append("얼굴형 분석 결과가 없어 헤어스타일을 추천할 수 없습니다.")
    else:
        hairstyle = recommend_hairstyle(face_shape["label"], diagnosis.get("samjeong"), gender)
        if not hairstyle["matched"]:
            warnings.append("hair.md에서 일치하는 추천 항목을 찾지 못했습니다.")

    makeup = recommend_makeup(diagnosis.get("personal_color") or {}, gender)
    if not makeup["matched"]:
        warnings.append("makeup.xlsx에서 일치하는 추천 항목을 찾지 못했습니다.")

    return {
        "image_path": diagnosis.get("image_path"),
        "gender":     gender,
        "hairstyle":  hairstyle,
        "makeup":     makeup,
        "warnings":   warnings,
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    sys.path.insert(0, str(_ROOT))
    from diagnose import diagnose  # noqa: E402

    p = argparse.ArgumentParser(description="얼굴 사진 1장 → 통합 진단 + 헤어스타일/메이크업 추천")
    p.add_argument("image", help="얼굴 사진 경로")
    p.add_argument("--gender", required=True, choices=["male", "female"],
                   help="hair.md 매칭에 사용할 성별")
    p.add_argument("--bundle", default=None, help="퍼스널컬러 모델 번들 경로 (기본: skin/model_bundle/)")
    p.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = p.parse_args()

    diagnose_kwargs = {}
    if args.bundle:
        diagnose_kwargs["bundle_dir"] = args.bundle

    diagnosis = diagnose(args.image, **diagnose_kwargs)
    result = recommend(diagnosis, gender=args.gender)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        print("=" * 56)
        print(f"  추천 결과 — {result['image_path']} ({result['gender']})")
        print("=" * 56)

        hs = result["hairstyle"]
        if hs:
            print(f"\n[헤어스타일] 얼굴형={hs['face_shape']} 삼정={hs['samjeong']}")
            print(f"  추천: {', '.join(hs['recommended']) or '-'}")
            print(f"  비추천: {', '.join(hs['not_recommended']) or '-'}")

        mk = result["makeup"]
        print(f"\n[메이크업] 퍼스널컬러={', '.join(mk['labels']) or '-'}")
        print(f"  추천: {', '.join(mk['recommended']) or '-'}")

        if result["warnings"]:
            print("\n[참고]")
            for w in result["warnings"]:
                print(f"  - {w}")
        print()
