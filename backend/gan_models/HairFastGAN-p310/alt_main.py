"""
alt_main.py - 오리지널 HairFastGAN + 자동 이미지 전처리
=========================================================

이 파일이 하는 일:
  1. 입력 이미지를 HairFastGAN이 요구하는 FFHQ 형식(1024x1024)으로 자동 변환
  2. HairFastGAN으로 헤어스타일과 머리 색상 합성
  3. 결과를 파일로 저장

pipeline.py와 다른 점:
  - FFHQ 정렬(눈 위치 기준 얼굴 각도/위치 보정)을 사용해 합성 품질이 더 높음
  - 대신 결과물이 원본과 구도가 달라짐 (얼굴 클로즈업 형태)
  - 안경 제거, 웜업, 캐싱 기능은 없음
  - 구조가 단순해서 이해하기 쉬움

사용법:
    python alt_main.py --face=input/man.jpg --shape=input/woman.png --output=output/result.png
    python alt_main.py --face=input/man.jpg --shape=input/woman.png --color=input/2.png --output=output/result.png

v2 변경: shape/color 이미지는 FFHQ 정렬 대신 center-crop을 사용하여 헤어 볼륨/텍스처 손실 방지.
"""
import os
import sys
import argparse
import scipy.ndimage          # FFHQ 정렬 내부에서 가우시안 블러에 사용
from pathlib import Path
from typing import Optional   # 반환값이 있을 수도, 없을 수도 있는 타입 표현용

# ===========================================================================
# [Windows 전용] CUDA 컴파일 환경 자동 설정
# ===========================================================================
# HairFastGAN은 처음 실행 시 PyTorch C++/CUDA 확장(fused_bias_act, upfirdn2d)을
# 자동으로 컴파일합니다. Windows에서는 이 과정이 아래 세 가지 이유로 실패하기 쉽습니다:
#   1. MSVC(Visual Studio C++) 헤더 경로가 환경변수에 없음
#   2. 이전에 잘못된 옵션으로 컴파일된 캐시 파일이 남아있음
#   3. CUDA 13.x CCCL 라이브러리가 특정 컴파일러 플래그를 요구함
# 아래 코드가 이 세 가지를 시작 시 자동으로 해결합니다.
if sys.platform == 'win32':
    import os as _os, shutil as _sh
    from pathlib import Path as _P

    # -----------------------------------------------------------------------
    # 해결 1: MSVC 헤더/라이브러리 경로 자동 탐색 및 환경변수 설정
    # -----------------------------------------------------------------------
    # conda 환경에서 python을 바로 실행하면 Visual Studio 경로(INCLUDE 환경변수)가
    # 설정되지 않아서 "cstddef: No such file" 같은 에러가 납니다.
    # → VS 설치 폴더를 직접 탐색해서 경로를 강제로 설정합니다.
    if 'INCLUDE' not in _os.environ:
        _includes: list[str] = []   # C++ 헤더 파일 경로들
        _libs: list[str] = []       # 라이브러리 파일 경로들

        # Visual Studio 버전(18=2025, 2022, 2019, 17=2017)과
        # 에디션(Community/Professional/Enterprise/BuildTools)을 순서대로 탐색
        for _vs_ver in ('18', '2022', '2019', '17'):
            for _edition in ('Community', 'Professional', 'Enterprise', 'BuildTools'):
                _msvc_root = _P(f"C:/Program Files/Microsoft Visual Studio/{_vs_ver}/{_edition}/VC/Tools/MSVC")
                if _msvc_root.exists():
                    _vers = sorted(_msvc_root.iterdir())
                    if _vers:
                        _mv = _vers[-1]   # 여러 버전이 있으면 가장 최신 사용
                        if (_mv / 'include').exists():
                            _includes.append(str(_mv / 'include'))
                        if (_mv / 'lib' / 'x64').exists():
                            _libs.append(str(_mv / 'lib' / 'x64'))
                        # cl.exe(C++ 컴파일러) 버전도 헤더와 일치시켜야 함
                        # PATH 맨 앞에 삽입해서 구버전 cl.exe보다 먼저 실행되게 함
                        _cl_dir = _mv / 'bin' / 'HostX64' / 'x64'
                        if _cl_dir.exists():
                            _os.environ['PATH'] = str(_cl_dir) + _os.pathsep + _os.environ.get('PATH', '')
                        print(f"[alt_main] MSVC: {_mv.name} ({_vs_ver}/{_edition})")
                    break
            if _includes:
                break

        # Windows SDK(ucrt, um 등 Windows API 헤더) 경로도 추가
        for _winsdk_root, _subs in (
            (_P("C:/Program Files (x86)/Windows Kits/10/Include"), ('ucrt', 'um', 'shared', 'winrt')),
            (_P("C:/Program Files (x86)/Windows Kits/10/Lib"),    ('ucrt/x64', 'um/x64')),
        ):
            if _winsdk_root.exists():
                _sv = sorted(_winsdk_root.iterdir())[-1]   # 최신 SDK 버전
                _target = _includes if 'Include' in str(_winsdk_root) else _libs
                for _sub in _subs:
                    _p = _sv / _sub
                    if _p.exists():
                        _target.append(str(_p))

        if _includes:
            _os.environ['INCLUDE'] = ';'.join(_includes)
            _os.environ['LIB']     = ';'.join(_libs)
            print(f"[alt_main] INCLUDE set ({len(_includes)} paths)")

    # -----------------------------------------------------------------------
    # 해결 2: 오래된 컴파일 캐시 삭제
    # -----------------------------------------------------------------------
    # PyTorch는 CUDA 확장을 컴파일한 결과를 캐시에 저장합니다.
    # 이전에 잘못된 옵션으로 컴파일된 캐시가 남아 있으면 새로 컴파일하지 않아서
    # 계속 에러가 납니다. → 시작할 때마다 캐시를 지워서 항상 올바르게 재컴파일합니다.
    # 캐시 폴더명에 Python 버전과 CUDA 버전이 포함됨 (예: py310_cu124, py311_cu124)
    import torch as _torch
    _py    = f"py{sys.version_info.major}{sys.version_info.minor}"
    _cu    = f"cu{''.join(_torch.version.cuda.split('.'))}" if _torch.cuda.is_available() else "cpu"
    _cache = _P.home() / f"AppData/Local/torch_extensions/Cache/{_py}_{_cu}"
    for _sub in ("fused", "upfirdn2d"):
        _d = _cache / _sub
        if _d.exists():
            _sh.rmtree(_d, ignore_errors=True)

    # -----------------------------------------------------------------------
    # 해결 3: CUDA 13.x CCCL 호환 컴파일러 플래그 자동 주입
    # -----------------------------------------------------------------------
    # CUDA 13.x 버전의 CCCL 라이브러리는 MSVC에 /Zc:preprocessor 플래그를 요구합니다.
    # PyTorch의 JIT 컴파일 함수(torch.utils.cpp_extension.load)가 기본으로 이 플래그를
    # 포함하지 않기 때문에, 함수를 우리가 만든 버전으로 교체(monkey-patch)합니다.
    import torch.utils.cpp_extension as _cext
    _orig_load = _cext.load

    def _patched_load(*_a, **_kw):
        # C++ 컴파일 플래그에 신규 전처리기 옵션 추가
        _cf = list(_kw.get('extra_cflags') or [])
        if '/Zc:preprocessor' not in _cf:
            _cf.append('/Zc:preprocessor')
        _kw['extra_cflags'] = _cf
        # CUDA 컴파일 플래그에 CCCL 경고 억제 옵션 추가
        _cu = list(_kw.get('extra_cuda_cflags') or [])
        if not any('CCCL_IGNORE' in _f for _f in _cu):
            _cu += ['-DCCCL_IGNORE_MSVC_TRADITIONAL_PREPROCESSOR_WARNING', '-Xcompiler=/Zc:preprocessor']
        _kw['extra_cuda_cflags'] = _cu
        return _orig_load(*_a, **_kw)

    _cext.load = _patched_load   # 원래 함수를 우리 버전으로 교체

# ===========================================================================
# 라이브러리 임포트
# ===========================================================================
import numpy as np                         # 이미지를 숫자 배열로 다룰 때 사용
import torch                               # PyTorch: 딥러닝 프레임워크
import dlib                                # 얼굴 감지 및 랜드마크 추출
from PIL import Image, ImageFilter, ImageEnhance   # 이미지 처리
from torchvision.utils import save_image   # 텐서를 이미지 파일로 저장

from hair_swap import HairFast, get_parser  # HairFastGAN 핵심 모델


# ===========================================================================
# FFHQ 정렬 (HairFastGAN 최적 입력 형식으로 변환)
# ===========================================================================

def _ffhq_align(img: Image.Image) -> Optional[Image.Image]:
    """
    FFHQ 스타일 얼굴 정렬을 수행합니다.

    FFHQ(Flickr-Faces-HQ)란?
      StyleGAN2가 학습한 고품질 얼굴 데이터셋입니다.
      이 데이터셋의 얼굴들은 모두 동일한 방식으로 정렬되어 있습니다:
        - 눈이 이미지의 특정 높이(약 y=420)에 위치
        - 얼굴이 정면을 향함
        - 얼굴이 가운데 중심
      HairFastGAN도 이 형식으로 학습되었기 때문에, 같은 형식으로 입력해야
      합성 품질이 좋습니다.

    작동 방식:
      utils/shape_predictor.py의 align_face() 함수를 사용합니다.
      내부적으로 dlib 68개 랜드마크(눈/코/입/윤곽)를 감지하고
      눈 위치를 기준으로 이미지를 회전/크기조정/이동해서
      표준 FFHQ 형식의 1024x1024 이미지로 만듭니다.

    반환:
      성공: 정렬된 1024x1024 PIL Image
      실패: None (얼굴 미감지, 파일 없음 등)
    """
    try:
        from utils.shape_predictor import align_face
        result = align_face([img], return_tensors=False)
        if result:
            return result[0]
    except Exception as e:
        print(f"[alt_main]   FFHQ 정렬 실패: {e}")
    return None


def _face_crop_resize(img: Image.Image) -> Optional[Image.Image]:
    """
    FFHQ 정렬이 실패했을 때 사용하는 대체 방법입니다.
    dlib으로 얼굴 위치를 감지하고, 40% 여유를 둬서 정사각형으로 크롭한 뒤
    1024x1024로 리사이즈합니다.

    언제 사용?
      - 얼굴 랜드마크 감지가 실패했지만 얼굴 위치(bbox)는 감지되는 경우
      - 옆모습이거나 얼굴이 많이 기울어진 경우

    40% 패딩 이유:
      얼굴 박스만 크롭하면 이마/머리카락이 잘립니다.
      얼굴 너비의 40%를 각 방향으로 여유를 줘서
      머리카락과 턱이 포함되도록 합니다.

    반환:
      성공: 1024x1024 PIL Image
      실패: None (얼굴 미감지)
    """
    try:
        detector = dlib.get_frontal_face_detector()
        dets = detector(np.array(img), 1)   # 1 = 업스케일 1회 (작은 얼굴도 감지)
        if not dets:
            return None
        # 여러 얼굴 감지 시 가장 큰 얼굴 선택
        det = max(dets, key=lambda d: d.width() * d.height())
        x1, y1, x2, y2 = det.left(), det.top(), det.right(), det.bottom()
        fw, fh = x2 - x1, y2 - y1

        # 얼굴 크기의 40%를 상하좌우 여유로 추가
        pad_x, pad_y = int(fw * 0.4), int(fh * 0.4)
        W, H = img.size
        cx1 = max(x1 - pad_x, 0); cy1 = max(y1 - pad_y, 0)
        cx2 = min(x2 + pad_x, W); cy2 = min(y2 + pad_y, H)

        # 정사각형으로 만들기 (긴 쪽 기준)
        side = max(cx2 - cx1, cy2 - cy1)
        mx, my = (cx1 + cx2) // 2, (cy1 + cy2) // 2
        sx1 = max(mx - side // 2, 0); sy1 = max(my - side // 2, 0)
        sx2 = min(sx1 + side, W);     sy2 = min(sy1 + side, H)

        return img.crop((sx1, sy1, sx2, sy2)).resize((1024, 1024), Image.LANCZOS)
    except Exception as e:
        print(f"[alt_main]   얼굴 크롭 실패: {e}")
        return None


def _center_crop(img: Image.Image) -> Image.Image:
    """
    얼굴 감지가 완전히 실패했을 때 사용하는 최후의 대체 방법입니다.
    이미지 중앙을 정사각형으로 크롭하고 1024x1024로 리사이즈합니다.

    단점: 얼굴이 중앙에 없으면 품질이 나빠질 수 있음.
    """
    W, H = img.size
    side = min(W, H)   # 짧은 쪽 기준으로 정사각형 크기 결정
    return img.crop(((W - side) // 2, (H - side) // 2,
                     (W + side) // 2, (H + side) // 2)
                    ).resize((1024, 1024), Image.LANCZOS)


def _sharpen(img: Image.Image) -> Image.Image:
    """
    작은 이미지를 1024x1024로 업스케일했을 때 생기는 뭉침(blur)을 보정합니다.

    처리 순서:
      1. UnsharpMask: 엣지(윤곽선)를 선명하게 만드는 필터
         - radius=2: 비교할 주변 픽셀 범위
         - percent=150: 선명도 강도 (100이 기본)
         - threshold=3: 최소 차이 (너무 작은 차이는 무시)
      2. Sharpness(1.3): 전체적인 선명도 1.3배 증가 (1.0이 원본)
    """
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    return ImageEnhance.Sharpness(img).enhance(1.3)


# ===========================================================================
# 이미지 전처리 메인 함수
# ===========================================================================

def prepare(path: Path, role: str) -> Image.Image:
    """
    입력 이미지를 HairFastGAN이 요구하는 1024x1024로 준비합니다.
    role에 따라 처리 방식이 다릅니다.

    인수:
        path: 이미지 파일 경로
        role: 'face' / 'shape' / 'color'

    [face 처리 흐름] — FFHQ 정렬 우선
        1순위: FFHQ 정렬 (얼굴 포즈/눈 위치 표준화, 합성 품질 핵심)
               ↳ 원본이 작은 이미지(< 1024px)였으면 정렬 후 추가로 샤프닝
        2순위 (큰 이미지, FFHQ 실패): 얼굴 bbox 크롭 (40% 패딩)
        3순위 (큰 이미지, 얼굴 미감지): 중앙 크롭
        4순위 (작은 이미지, FFHQ 실패): LANCZOS 업스케일 + 샤프닝

    [shape / color 처리 흐름] — center-crop만 사용
        FFHQ 정렬을 적용하지 않습니다.
        이유: 헤어가 프레임을 가득 채우는 클로즈업 이미지에 FFHQ 정렬을 적용하면
        정렬 알고리즘이 머리 위 여백을 표준 비율로 맞추려다 원본에 없는 영역을
        가우시안 블러로 패딩합니다. 이 블러 패치가 헤어 볼륨 상단을 덮어 합성 결과의
        헤어 볼륨/텍스처를 크게 손상시킵니다.
        → center-crop + LANCZOS 리사이즈만 적용해 헤어 디테일을 보존합니다.
        샤프닝도 적용하지 않습니다 (헤어 텍스처에 halo 아티팩트 유발 가능).
    """
    # RGBA(투명도 포함 PNG), 흑백 등 모든 형식을 RGB로 통일
    img = Image.open(path).convert('RGB')
    w, h = img.size

    # ------------------------------------------------------------------
    # shape / color: center-crop만 적용 (FFHQ 정렬 건너뜀)
    # ------------------------------------------------------------------
    if role in ('shape', 'color'):
        print(f"[alt_main] {role}: {w}x{h} - center-crop 리사이즈 (FFHQ 정렬 건너뜀)")
        result = _center_crop(img)
        print(f"[alt_main] {role}: center-crop 완료")
        return result

    # ------------------------------------------------------------------
    # face: FFHQ 정렬 우선, 실패 시 폴백
    # ------------------------------------------------------------------
    need_upscale = w < 1024 or h < 1024   # 작은 이미지 여부 체크

    print(f"[alt_main] {role}: {w}x{h} - FFHQ 정렬 시도")

    # 1순위: FFHQ 정렬
    aligned = _ffhq_align(img)
    if aligned is not None:
        # 작은 이미지에서 업스케일된 경우 추가 샤프닝으로 뭉침 보정
        result = _sharpen(aligned) if need_upscale else aligned
        print(f"[alt_main] {role}: FFHQ 정렬 완료")
        return result

    # FFHQ 정렬 실패 시 이미지 크기에 따라 다른 방법 사용
    if not need_upscale:
        # 큰 이미지: 얼굴 영역 감지 후 크롭
        cropped = _face_crop_resize(img)
        if cropped is not None:
            print(f"[alt_main] {role}: 얼굴 크롭 폴백")
            return cropped
        # 얼굴도 못 찾으면 중앙 크롭
        print(f"[alt_main] {role}: 중앙 크롭 폴백")
        return _center_crop(img)

    # 작은 이미지: 업스케일 + 샤프닝
    print(f"[alt_main] {role}: LANCZOS 업스케일 폴백")
    return _sharpen(img.resize((1024, 1024), Image.LANCZOS))


# ===========================================================================
# 메인 실행 함수
# ===========================================================================

def main():
    """
    명령줄 인수를 받아서 전처리 → 합성 → 저장을 순서대로 실행합니다.

    처리 흐름:
      1. 인수 파싱 (--face, --shape, [--color], --output)
      2. GPU/CPU 자동 선택
      3. face/shape/[color] 이미지 각각 FFHQ 전처리
      4. HairFastGAN으로 헤어 합성
      5. 결과 저장

    --color를 생략하면 shape 이미지를 color로도 사용합니다.
    이 경우 HairFastGAN 내부에서 color 합성 단계가 자동으로 건너뛰어집니다.
    """
    # HairFastGAN 자체 인수 파서 (--size, --ckpt 등 모델 설정)
    model_parser = get_parser()

    # 우리가 추가하는 인수 파서 (--face, --shape, [--color], --output)
    parser = argparse.ArgumentParser(
        description='HairFastGAN - 오리지널 기능 + 자동 전처리',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--face',   type=Path, required=True,
                        help='헤어스타일을 바꿀 얼굴 이미지 경로')
    parser.add_argument('--shape',  type=Path, required=True,
                        help='원하는 헤어스타일 모양 참조 이미지 경로')
    parser.add_argument('--color',  type=Path, default=None,
                        help='원하는 머리 색상 참조 이미지 경로 (생략 시 shape 이미지 색상 유지)')
    parser.add_argument('--output', type=Path, default=Path('output/result.png'),
                        help='결과 저장 경로')

    # parse_known_args: 모르는 인수는 remaining에 넘겨서 model_parser가 처리하게 함
    args, remaining = parser.parse_known_args()
    model_args, _   = model_parser.parse_known_args(remaining)

    # 결과 저장 폴더가 없으면 자동으로 생성
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # GPU(CUDA) 사용 가능하면 GPU, 없으면 CPU 자동 선택
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"[alt_main] Device: {device}")
    model_args.device = device

    # 세 이미지를 각각 FFHQ 형식으로 전처리
    # (face만 합성 대상, shape는 헤어 모양 참조, color는 색상 참조)
    face_img  = prepare(args.face,  'face')
    shape_img = prepare(args.shape, 'shape')

    if args.color is not None:
        # --color 지정 시: 별도 이미지에서 색상 추출
        color_img = prepare(args.color, 'color')
    else:
        # --color 생략 시: shape와 동일 객체를 넘기면 HairFastGAN 내부에서
        # color 합성 단계(shape_module 호출)를 자동으로 건너뜀
        color_img = shape_img
        print("[alt_main] --color 미지정: 색상 합성 건너뜀 (shape 색상 그대로 적용)")

    # HairFastGAN 모델 초기화 및 합성 실행
    # 처음 실행 시 CUDA 커널 컴파일로 수 분이 걸릴 수 있음
    model  = HairFast(model_args)
    result = model.swap(face_img, shape_img, color_img)
    # result: PyTorch 텐서 형태 (채널, 높이, 너비), 값 범위 0~1

    # 텐서를 이미지 파일로 저장
    save_image(result, str(args.output))
    print(f"[alt_main] 완료 -> {args.output}")


if __name__ == '__main__':
    main()
