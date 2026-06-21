import os
import sys
import uuid
import threading
from pathlib import Path

import numpy as np
from PIL import Image

_lock = threading.Lock()
_hair_fast = None

HAIRFASTGAN_DIR = Path(__file__).resolve().parent.parent.parent / 'gan_models' / 'HairFastGAN-p310'

REFERENCE_IMAGES = [
    {'path': str(HAIRFASTGAN_DIR / 'imgs' / 'hair' / 'MH1.jpg'), 'name': '헤어스타일 1'},
    {'path': str(HAIRFASTGAN_DIR / 'imgs' / 'hair' / 'MH2.jpg'), 'name': '헤어스타일 2'},
    {'path': str(HAIRFASTGAN_DIR / 'imgs' / 'hair' / 'MH3.jpg'), 'name': '헤어스타일 3'},
]

_FRONTEND_PUBLIC = Path(__file__).resolve().parent.parent.parent.parent / 'frontend' / 'public'


def _resolve_reference_images(ref_images: list) -> list:
    resolved = []
    for ref in ref_images:
        url = ref.get('url') or ''
        name = ref.get('name') or ''
        if not url:
            continue
        if url.startswith('/'):
            local = _FRONTEND_PUBLIC / url.lstrip('/')
            if local.exists():
                resolved.append({'path': str(local), 'name': name})
    return resolved if resolved else REFERENCE_IMAGES


def _get_hair_fast():
    global _hair_fast
    if _hair_fast is not None:
        return _hair_fast

    os.chdir(HAIRFASTGAN_DIR)
    if str(HAIRFASTGAN_DIR) not in sys.path:
        sys.path.insert(0, str(HAIRFASTGAN_DIR))

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


def run_hair(source_path: str, output_dir: str, reference_images: list | None = None) -> list:
    with _lock:
        return _run_hair_inner(source_path, output_dir, reference_images)


def _run_hair_inner(source_path: str, output_dir: str, reference_images: list | None = None) -> list:
    hair_fast = _get_hair_fast()
    os.makedirs(output_dir, exist_ok=True)
    results = []

    refs = _resolve_reference_images(reference_images) if reference_images else REFERENCE_IMAGES
    for ref in refs:
        result = hair_fast.swap(
            face_img=source_path,
            shape_img=ref['path'],
            color_img=source_path,
            align=True,
        )
        result_tensor = result[0] if isinstance(result, tuple) else result
        img_np = (result_tensor.permute(1, 2, 0).cpu().clamp(0, 1).numpy() * 255).astype(np.uint8)
        img = Image.fromarray(img_np)

        filename = f"hair_{uuid.uuid4().hex[:8]}.png"
        out_path = os.path.join(output_dir, filename)
        img.save(out_path)
        results.append({'image_path': out_path, 'name': ref['name']})

    return results
