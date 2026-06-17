import os
import sys
import uuid
import threading
from pathlib import Path

import numpy as np
from PIL import Image

_lock = threading.Lock()
_hair_fast = None

HAIRFASTGAN_DIR = Path(__file__).resolve().parent.parent / 'gan_models' / 'HairFastGAN-p310'

REFERENCE_IMAGES = [
    {'path': str(HAIRFASTGAN_DIR / 'imgs' / 'hair' / 'MH1.jpg'), 'name': '헤어스타일 1'},
    # 테스트 후 아래 2개 주석 해제
    # {'path': str(HAIRFASTGAN_DIR / 'imgs' / 'hair' / 'MH2.jpg'), 'name': '헤어스타일 2'},
    # {'path': str(HAIRFASTGAN_DIR / 'imgs' / 'hair' / 'MH3.jpg'), 'name': '헤어스타일 3'},
]


def _get_hair_fast():
    global _hair_fast
    if _hair_fast is not None:
        return _hair_fast

    # pretrained_models/ 상대경로 해결을 위해 CWD 변경 (모델 로드 시 1회만)
    os.chdir(HAIRFASTGAN_DIR)
    if str(HAIRFASTGAN_DIR) not in sys.path:
        sys.path.insert(0, str(HAIRFASTGAN_DIR))

    # CPU 환경에서 map_location 미지정 torch.load 오류 방지 패치
    import torch
    _orig_load = torch.load
    def _patched_load(f, map_location=None, **kwargs):
        if map_location is None:
            map_location = 'cpu'
        return _orig_load(f, map_location=map_location, **kwargs)
    torch.load = _patched_load

    from hair_swap import HairFast, get_parser
    args = get_parser().parse_args([])
    _hair_fast = HairFast(args)
    return _hair_fast


def run_hair(source_path: str, output_dir: str) -> list:
    with _lock:
        return _run_hair_inner(source_path, output_dir)


def _run_hair_inner(source_path: str, output_dir: str) -> list:
    hair_fast = _get_hair_fast()
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for ref in REFERENCE_IMAGES:
        result = hair_fast.swap(
            face_img=source_path,
            shape_img=ref['path'],
            color_img=ref['path'],
            align=True,
        )
        # align=True 시 (final_image, face, shape, color) 튜플 반환
        result_tensor = result[0] if isinstance(result, tuple) else result
        # swap() 출력: float [0, 1], shape [C, H, W]
        img_np = (result_tensor.permute(1, 2, 0).cpu().clamp(0, 1).numpy() * 255).astype(np.uint8)
        img = Image.fromarray(img_np)

        filename = f"hair_{uuid.uuid4().hex[:8]}.png"
        out_path = os.path.join(output_dir, filename)
        img.save(out_path)
        results.append({'image_path': out_path, 'name': ref['name']})

    return results
