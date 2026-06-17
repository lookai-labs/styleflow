"""
test_compare.py - shape 전처리 방식 차이가 합성 결과에 미치는 영향 비교
======================================================================
test.py로 생성한 output/debug/ 이미지들을 그대로 사용해
FFHQ 정렬 shape vs 단순 리사이즈 shape 두 가지를 실제 HairFastGAN으로 합성하고 비교한다.

입력 (output/debug/ 에서 로드):
  debug_face_final.png          - face 이미지 (전처리 완료)
  debug_shape_aligned.png       - shape (FFHQ 정렬 버전, 현재 alt_main.py 동작)
  debug_shape_simple_resize.png - shape (단순 LANCZOS 리사이즈 버전, 비교 대상)

출력 (output/compare/):
  result_A_ffhq_aligned.png     - Variant A 합성 결과
  result_B_simple_resize.png    - Variant B 합성 결과
"""
import sys

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
                        print(f"[compare] MSVC: {_mv.name} ({_vs_ver}/{_edition})")
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
            print(f"[compare] INCLUDE set ({len(_includes)} paths)")

    # -----------------------------------------------------------------------
    # 해결 2: 오래된 컴파일 캐시 삭제
    # -----------------------------------------------------------------------
    # PyTorch는 CUDA 확장을 컴파일한 결과를 캐시에 저장합니다.
    # 이전에 잘못된 옵션으로 컴파일된 캐시가 남아 있으면 새로 컴파일하지 않아서
    # 계속 에러가 납니다. → 시작할 때마다 캐시를 지워서 항상 올바르게 재컴파일합니다.
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
        _cf = list(_kw.get('extra_cflags') or [])
        if '/Zc:preprocessor' not in _cf:
            _cf.append('/Zc:preprocessor')
        _kw['extra_cflags'] = _cf
        _cu = list(_kw.get('extra_cuda_cflags') or [])
        if not any('CCCL_IGNORE' in _f for _f in _cu):
            _cu += ['-DCCCL_IGNORE_MSVC_TRADITIONAL_PREPROCESSOR_WARNING', '-Xcompiler=/Zc:preprocessor']
        _kw['extra_cuda_cflags'] = _cu
        return _orig_load(*_a, **_kw)

    _cext.load = _patched_load


# ===========================================================================
# 라이브러리 임포트 (CUDA 패치 블록 이후에 위치해야 함)
# ===========================================================================
import torch
from pathlib import Path
from PIL import Image
import torchvision.transforms.functional as F
from torchvision.utils import save_image

from hair_swap import HairFast, get_parser


# ===========================================================================
# 고정 경로 설정
# ===========================================================================
DEBUG_DIR   = Path('output/debug')
COMPARE_DIR = Path('output/compare')

FACE_PATH    = DEBUG_DIR / 'debug_face_final.png'
FACE_C_PATH  = DEBUG_DIR / 'debug_face_aligned_raw.png'    # 샤프닝 전 face (Variant C용)
SHAPE_A_PATH = DEBUG_DIR / 'debug_shape_aligned.png'       # FFHQ 정렬 버전
SHAPE_B_PATH = DEBUG_DIR / 'debug_shape_simple_resize.png' # 단순 리사이즈 버전

OUT_A = COMPARE_DIR / 'result_A_ffhq_aligned.png'
OUT_B = COMPARE_DIR / 'result_B_simple_resize.png'
OUT_C = COMPARE_DIR / 'result_C_face_unsharpened.png'


def load_as_tensor(path: Path) -> torch.Tensor:
    """PIL Image(RGB) → float32 텐서 [0, 1]"""
    return F.to_tensor(Image.open(path).convert('RGB'))


def main():
    # 입력 파일 존재 확인
    for p in (FACE_PATH, FACE_C_PATH, SHAPE_A_PATH, SHAPE_B_PATH):
        if not p.exists():
            print(f"[오류] 파일 없음: {p}")
            print("  먼저 test.py를 실행해서 output/debug/ 파일을 생성하세요.")
            return

    COMPARE_DIR.mkdir(parents=True, exist_ok=True)

    # Device 설정
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"[compare] Device: {device}")

    # 입력 이미지 로드 (1024x1024 전처리 완료 상태 — 추가 전처리 없음)
    print("[compare] 입력 이미지 로드 중...")
    face_tensor    = load_as_tensor(FACE_PATH)
    face_c_tensor  = load_as_tensor(FACE_C_PATH)
    shape_a_tensor = load_as_tensor(SHAPE_A_PATH)
    shape_b_tensor = load_as_tensor(SHAPE_B_PATH)
    print(f"  face    : {FACE_PATH.name}  {tuple(face_tensor.shape)}")
    print(f"  faceC   : {FACE_C_PATH.name}  {tuple(face_c_tensor.shape)}")
    print(f"  shapeA  : {SHAPE_A_PATH.name}  {tuple(shape_a_tensor.shape)}")
    print(f"  shapeB  : {SHAPE_B_PATH.name}  {tuple(shape_b_tensor.shape)}")

    # 모델 초기화 (한 번만 — 두 variant가 공유)
    print("[compare] HairFast 모델 초기화 중... (CUDA 커널 컴파일 포함, 수 분 소요 가능)")
    model_args = get_parser().parse_args([])
    model_args.device = device
    model = HairFast(model_args)
    print("[compare] 모델 초기화 완료")

    # ------------------------------------------------------------------
    # Variant A: 현재 alt_main.py와 동일한 입력 (FFHQ 정렬 shape)
    # ------------------------------------------------------------------
    print("\n[1/3] Variant A (FFHQ 정렬 shape) 합성 중...")
    result_a = model.swap(face_tensor, shape_a_tensor, shape_a_tensor)
    save_image(result_a, str(OUT_A))
    print(f"  완료 -> {OUT_A}")

    # ------------------------------------------------------------------
    # Variant B: 단순 LANCZOS 리사이즈 shape (FFHQ 정렬 없음)
    # ------------------------------------------------------------------
    print("\n[2/3] Variant B (단순 리사이즈 shape) 합성 중...")
    result_b = model.swap(face_tensor, shape_b_tensor, shape_b_tensor)
    save_image(result_b, str(OUT_B))
    print(f"  완료 -> {OUT_B}")

    # ------------------------------------------------------------------
    # Variant C: face 샤프닝 제거 + 단순 리사이즈 shape
    # A·B의 이중선이 face _sharpen() 때문인지 모델 한계인지 구분
    # ------------------------------------------------------------------
    print("\n[3/3] Variant C (face 샤프닝 제거 + 단순 리사이즈 shape) 합성 중...")
    result_c = model.swap(face_c_tensor, shape_b_tensor, shape_b_tensor)
    save_image(result_c, str(OUT_C))
    print(f"  완료 -> {OUT_C}")

    # 결과 요약
    print(f"\n{'='*50}")
    print("  생성된 비교 파일")
    print(f"{'='*50}")
    print(f"  A (FFHQ 정렬, 샤프닝됨)          : {OUT_A}")
    print(f"  B (단순 리사이즈, 샤프닝됨)        : {OUT_B}")
    print(f"  C (단순 리사이즈, 샤프닝 제거)     : {OUT_C}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
