"""
test.py - alt_main.py 전처리 단계 디버깅 스크립트
==================================================
HairFastGAN 합성(모델/CUDA 로딩) 없이 전처리 결과만 빠르게 시각 확인합니다.

확인 목적:
  1. shape 이미지가 헤어 클로즈업일 때 FFHQ 정렬이 헤어 디테일을 얼마나 손상시키는지
  2. face 이미지가 작을 때 _sharpen() UnsharpMask가 헤어라인에 halo를 만드는지

사용법:
    python test.py --face=input/man.jpg --shape=input/woman.png

결과: output/debug/ 폴더에 비교용 이미지 저장
"""
import argparse
import scipy.ndimage          # FFHQ 정렬 내부 가우시안 블러에 필요 (align_face 호출 전에 import)
from pathlib import Path
from typing import Optional

import numpy as np
import dlib
from PIL import Image, ImageFilter, ImageEnhance


# ===========================================================================
# alt_main.py에서 복사한 전처리 함수들
# (HairFast 모델/CUDA 없이 독립 실행을 위해 그대로 복사, 로그 prefix만 변경)
# ===========================================================================

def _ffhq_align(img: Image.Image) -> Optional[Image.Image]:
    """dlib 68개 랜드마크 기반 FFHQ 정렬. 실패 시 None 반환."""
    try:
        from utils.shape_predictor import align_face
        result = align_face([img], return_tensors=False)
        if result:
            return result[0]
    except Exception as e:
        print(f"    FFHQ 정렬 실패: {e}")
    return None


def _face_crop_resize(img: Image.Image) -> Optional[Image.Image]:
    """dlib bbox 감지 → 40% 패딩 → 정사각형 크롭 → 1024x1024."""
    try:
        detector = dlib.get_frontal_face_detector()
        dets = detector(np.array(img), 1)
        if not dets:
            return None
        det = max(dets, key=lambda d: d.width() * d.height())
        x1, y1, x2, y2 = det.left(), det.top(), det.right(), det.bottom()
        fw, fh = x2 - x1, y2 - y1
        pad_x, pad_y = int(fw * 0.4), int(fh * 0.4)
        W, H = img.size
        cx1 = max(x1 - pad_x, 0); cy1 = max(y1 - pad_y, 0)
        cx2 = min(x2 + pad_x, W); cy2 = min(y2 + pad_y, H)
        side = max(cx2 - cx1, cy2 - cy1)
        mx, my = (cx1 + cx2) // 2, (cy1 + cy2) // 2
        sx1 = max(mx - side // 2, 0); sy1 = max(my - side // 2, 0)
        sx2 = min(sx1 + side, W);     sy2 = min(sy1 + side, H)
        return img.crop((sx1, sy1, sx2, sy2)).resize((1024, 1024), Image.LANCZOS)
    except Exception as e:
        print(f"    얼굴 크롭 실패: {e}")
        return None


def _center_crop(img: Image.Image) -> Image.Image:
    """중앙 정사각형 크롭 → 1024x1024 (최후 폴백)."""
    W, H = img.size
    side = min(W, H)
    return img.crop(((W - side) // 2, (H - side) // 2,
                     (W + side) // 2, (H + side) // 2)
                    ).resize((1024, 1024), Image.LANCZOS)


def _sharpen(img: Image.Image) -> Image.Image:
    """UnsharpMask(r=2, p=150, t=3) + Sharpness(1.3) — 업스케일 후 뭉침 보정."""
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    return ImageEnhance.Sharpness(img).enhance(1.3)


def prepare(path: Path, role: str) -> Image.Image:
    """
    alt_main.py의 prepare()와 동일한 로직.
    1순위: FFHQ 정렬 (작으면 + 샤프닝)
    2순위: 얼굴 크롭 (큰 이미지, FFHQ 실패)
    3순위: 중앙 크롭 (큰 이미지, 얼굴 미감지)
    4순위: 업스케일 + 샤프닝 (작은 이미지, FFHQ 실패)
    """
    img = Image.open(path).convert('RGB')
    w, h = img.size
    need_upscale = w < 1024 or h < 1024

    aligned = _ffhq_align(img)
    if aligned is not None:
        return _sharpen(aligned) if need_upscale else aligned

    if not need_upscale:
        cropped = _face_crop_resize(img)
        if cropped is not None:
            return cropped
        return _center_crop(img)

    return _sharpen(img.resize((1024, 1024), Image.LANCZOS))


# ===========================================================================
# 디버그 분석 함수
# ===========================================================================

def _save(img: Image.Image, path: Path, label: str, saved: list) -> None:
    """이미지를 저장하고 목록에 추가."""
    img.save(str(path))
    saved.append(path)
    print(f"    저장: {path.name}  ({label})")


def debug_face(path: Path, out_dir: Path) -> list:
    """
    face 이미지 분석.

    저장 파일:
      debug_face_aligned_raw.png       — FFHQ 정렬 직후 (샤프닝 전)
      debug_face_aligned_sharpened.png — 샤프닝 적용 후
      debug_face_final.png             — prepare() 최종 결과

    비교 포인트:
      raw vs sharpened: UnsharpMask가 헤어라인 경계에 halo를 만드는지 확인
    """
    saved = []
    img = Image.open(path).convert('RGB')
    w, h = img.size
    need_upscale = w < 1024 or h < 1024

    print(f"\n{'─'*50}")
    print(f"  [face]  경로: {path}")
    print(f"  원본 크기   : {w} x {h}")
    print(f"  need_upscale: {need_upscale}  ({'작은 이미지 → 샤프닝 경로' if need_upscale else '큰 이미지 → 샤프닝 없음'})")

    # FFHQ 정렬 시도
    print("  FFHQ 정렬 시도 중...")
    aligned = _ffhq_align(img)
    ffhq_ok = aligned is not None
    print(f"  FFHQ 정렬  : {'✓ 성공' if ffhq_ok else '✗ 실패'}")

    if ffhq_ok:
        # 샤프닝 전/후 두 버전 — need_upscale 여부와 무관하게 둘 다 저장
        _save(aligned,          out_dir / "debug_face_aligned_raw.png",       "FFHQ 정렬, 샤프닝 전", saved)
        _save(_sharpen(aligned), out_dir / "debug_face_aligned_sharpened.png", "FFHQ 정렬, 샤프닝 후", saved)
    else:
        print("    FFHQ 실패 → raw / sharpened 비교 파일 생성 불가")

    # prepare() 최종 결과 (실제 HairFastGAN에 들어가는 이미지)
    print("  prepare() 실행 중...")
    final = prepare(path, 'face')
    _save(final, out_dir / "debug_face_final.png", "prepare() 최종 출력", saved)

    return saved


def debug_shape(path: Path, out_dir: Path) -> list:
    """
    shape 이미지 분석.

    저장 파일:
      debug_shape_aligned.png      — FFHQ 정렬 결과
      debug_shape_simple_resize.png — 단순 LANCZOS 리사이즈 (FFHQ 없이)
      debug_shape_final.png         — prepare() 최종 결과

    비교 포인트:
      aligned vs simple_resize: FFHQ 정렬이 헤어 볼륨/디테일을 얼마나 손상시키는지 확인
    """
    saved = []
    img = Image.open(path).convert('RGB')
    w, h = img.size
    need_upscale = w < 1024 or h < 1024

    print(f"\n{'─'*50}")
    print(f"  [shape] 경로: {path}")
    print(f"  원본 크기   : {w} x {h}")
    print(f"  need_upscale: {need_upscale}  ({'작은 이미지 → 샤프닝 경로' if need_upscale else '큰 이미지 → 샤프닝 없음'})")

    # (a) FFHQ 정렬 결과
    print("  FFHQ 정렬 시도 중...")
    aligned = _ffhq_align(img)
    ffhq_ok = aligned is not None
    print(f"  FFHQ 정렬  : {'✓ 성공' if ffhq_ok else '✗ 실패'}")

    if ffhq_ok:
        _save(aligned, out_dir / "debug_shape_aligned.png", "FFHQ 정렬 결과", saved)
    else:
        print("    FFHQ 실패 → aligned 파일 생성 불가")

    # (b) 단순 LANCZOS 리사이즈 (FFHQ 정렬 없이) — 항상 생성
    simple = img.resize((1024, 1024), Image.LANCZOS)
    _save(simple, out_dir / "debug_shape_simple_resize.png", "단순 LANCZOS 리사이즈", saved)

    # prepare() 최종 결과
    print("  prepare() 실행 중...")
    final = prepare(path, 'shape')
    _save(final, out_dir / "debug_shape_final.png", "prepare() 최종 출력", saved)

    return saved


# ===========================================================================
# 메인
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description='alt_main.py 전처리 디버그 스크립트 (모델/CUDA 로딩 없음)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--face',  type=Path, required=True, help='face 이미지 경로')
    parser.add_argument('--shape', type=Path, required=True, help='shape 이미지 경로')
    args = parser.parse_args()

    out_dir = Path('output/debug')
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("  alt_main.py 전처리 디버그")
    print("  출력 폴더:", out_dir.resolve())
    print("=" * 50)

    all_saved = []
    all_saved += debug_face(args.face, out_dir)
    all_saved += debug_shape(args.shape, out_dir)

    print(f"\n{'='*50}")
    print(f"  생성된 파일 ({len(all_saved)}개)")
    print(f"{'='*50}")
    for f in all_saved:
        print(f"  {f}")


if __name__ == '__main__':
    main()
