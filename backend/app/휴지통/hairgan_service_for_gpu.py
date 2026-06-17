import gc
import os
import sys
import uuid
import threading
from pathlib import Path

import cv2
import dlib
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image

_lock      = threading.Lock()
_hair_fast = None
_detector  = None
_sp        = None

BASE_DIR        = Path(__file__).resolve().parent.parent
HAIRFASTGAN_DIR = BASE_DIR / 'gan_models' / 'HairFastGAN-p310'
BEAUTYGAN_DIR   = BASE_DIR / 'gan_models' / 'BeautyGAN-master-p310'
LANDMARK_PATH   = str(BEAUTYGAN_DIR / 'models' / 'shape_predictor_5_face_landmarks.dat')
BISENET_PTH     = str(HAIRFASTGAN_DIR / 'pretrained_models' / 'BiSeNet' / 'face_parsing_79999_iter.pth')

REFERENCE_IMAGES = [
    {'path': str(HAIRFASTGAN_DIR / 'imgs' / 'hair' / 'MH1.jpg'), 'name': '헤어스타일 1'},
    # 테스트 후 아래 2개 주석 해제
    # {'path': str(HAIRFASTGAN_DIR / 'imgs' / 'hair' / 'MH2.jpg'), 'name': '헤어스타일 2'},
    # {'path': str(HAIRFASTGAN_DIR / 'imgs' / 'hair' / 'MH3.jpg'), 'name': '헤어스타일 3'},
]


def _init_dlib():
    global _detector, _sp
    if _detector is None:
        _detector = dlib.get_frontal_face_detector()
        _sp       = dlib.shape_predictor(LANDMARK_PATH)


def _init_hairfast():
    global _hair_fast
    if _hair_fast is not None:
        return

    os.chdir(HAIRFASTGAN_DIR)
    if str(HAIRFASTGAN_DIR) not in sys.path:
        sys.path.insert(0, str(HAIRFASTGAN_DIR))

    _orig_load = torch.load
    def _patched_load(f, map_location=None, **kw):
        return _orig_load(f, map_location=map_location or 'cpu', **kw)
    torch.load = _patched_load

    from hair_swap import HairFast, get_parser
    args = get_parser().parse_args([])
    _hair_fast = HairFast(args)


def _run_bisenet(orig_np, ow, oh):
    """BiSeNet 추론 후 모델을 즉시 해제해 메모리 확보."""
    os.chdir(HAIRFASTGAN_DIR)
    if str(HAIRFASTGAN_DIR) not in sys.path:
        sys.path.insert(0, str(HAIRFASTGAN_DIR))

    _orig_load = torch.load
    def _patched_load(f, map_location=None, **kw):
        return _orig_load(f, map_location=map_location or 'cpu', **kw)
    torch.load = _patched_load

    from models.CtrlHair.external_code.face_parsing.model import BiSeNet
    bisenet = BiSeNet(n_classes=19)
    bisenet.load_state_dict(torch.load(BISENET_PTH))
    bisenet.eval()

    to_tensor = T.Compose([
        T.ToTensor(),
        T.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ])
    img_512 = Image.fromarray(orig_np).resize((512, 512), Image.BILINEAR)
    img_t   = to_tensor(img_512).unsqueeze(0)

    with torch.no_grad():
        out     = bisenet(img_t)[0]
        parsing = out.squeeze(0).cpu().numpy().argmax(0)

    # BiSeNet 즉시 해제
    del bisenet, img_t, out
    gc.collect()

    parsing_orig = cv2.resize(parsing.astype(np.uint8), (ow, oh), interpolation=cv2.INTER_NEAREST)
    return (parsing_orig == 17).astype(np.uint8) * 255


def _fill_hair(orig_bgr, hair_mask):
    kernel_size = 9
    kernel      = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    remove_mask = cv2.dilate(hair_mask, kernel, iterations=1)
    remove_mask = cv2.morphologyEx(remove_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    remove_bool = remove_mask > 0

    _, labels = cv2.distanceTransformWithLabels(
        remove_mask, distanceType=cv2.DIST_L2, maskSize=5, labelType=cv2.DIST_LABEL_PIXEL,
    )
    known_yx    = np.column_stack(np.where(remove_mask == 0))
    nearest_idx = np.clip(labels - 1, 0, len(known_yx) - 1)
    nearest_y   = known_yx[nearest_idx, 0]
    nearest_x   = known_yx[nearest_idx, 1]

    filled             = orig_bgr.copy()
    filled[remove_bool] = orig_bgr[nearest_y[remove_bool], nearest_x[remove_bool]]

    soft_alpha = cv2.GaussianBlur(remove_mask.astype(np.float32) / 255.0, (7, 7), 0)
    soft_alpha = np.clip(soft_alpha, 0.0, 1.0)[:, :, None]
    return (filled.astype(np.float32) * soft_alpha + orig_bgr.astype(np.float32) * (1.0 - soft_alpha)).astype(np.uint8)


def _composite(orig_np, prepped_bgr, result_np):
    oh, ow = orig_np.shape[:2]

    dets_orig = _detector(orig_np, 1)
    if not dets_orig:
        raise RuntimeError('원본 이미지에서 얼굴을 찾지 못했습니다.')
    lm_orig = _sp(orig_np, dets_orig[0])
    src_pts = np.array([[lm_orig.part(j).x, lm_orig.part(j).y] for j in range(5)], dtype=np.float64)

    dets_result = _detector(result_np, 1)
    if not dets_result:
        raise RuntimeError('GAN 결과 이미지에서 얼굴을 찾지 못했습니다.')
    lm_result = _sp(result_np, dets_result[0])
    dst_pts   = np.array([[lm_result.part(j).x, lm_result.part(j).y] for j in range(5)], dtype=np.float64)

    M, _ = cv2.estimateAffinePartial2D(dst_pts, src_pts, method=cv2.LMEDS)
    if M is None:
        raise RuntimeError('Affine 변환 행렬 계산 실패')

    warped = cv2.warpAffine(result_np, M, (ow, oh), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    fr = dets_result[0]
    fx1, fy1, fx2, fy2 = fr.left(), fr.top(), fr.right(), fr.bottom()
    face_w  = fx2 - fx1
    face_h  = fy2 - fy1
    cx      = (fx1 + fx2) // 2
    hair_cy = int((fy1 + fy2) / 2 - face_h * 0.35)
    rx      = int(face_w * 1.50)
    ry      = int(face_h * 1.30)

    gan_h, gan_w = result_np.shape[:2]
    head_mask    = np.zeros((gan_h, gan_w), dtype=np.uint8)
    cv2.ellipse(head_mask, (cx, hair_cy), (rx, ry), 0, 0, 360, 255, -1)

    head_mask_warped = cv2.warpAffine(head_mask, M, (ow, oh), flags=cv2.INTER_NEAREST,
                                       borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    mask_kernel      = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    head_mask_warped = cv2.morphologyEx(head_mask_warped, cv2.MORPH_CLOSE, mask_kernel, iterations=1)

    mask_pts = cv2.findNonZero(head_mask_warped)
    if mask_pts is None:
        raise RuntimeError('합성 마스크가 비어 있습니다.')
    bx, by, bw, bh = cv2.boundingRect(mask_pts)
    center = (bx + bw // 2, by + bh // 2)

    warped_bgr  = cv2.cvtColor(warped, cv2.COLOR_RGB2BGR)
    blended_bgr = cv2.seamlessClone(warped_bgr, prepped_bgr, head_mask_warped, center, cv2.NORMAL_CLONE)
    return cv2.cvtColor(blended_bgr, cv2.COLOR_BGR2RGB)


def run_hair(source_path: str, output_dir: str) -> list:
    with _lock:
        return _run_hair_inner(source_path, output_dir)


def _run_hair_inner(source_path: str, output_dir: str) -> list:
    os.makedirs(output_dir, exist_ok=True)
    _init_dlib()

    orig_np  = dlib.load_rgb_image(source_path)
    oh, ow   = orig_np.shape[:2]
    orig_bgr = cv2.cvtColor(np.array(orig_np), cv2.COLOR_RGB2BGR)

    # 1. BiSeNet 추론 → 즉시 해제
    hair_mask   = _run_bisenet(orig_np, ow, oh)
    prepped_bgr = _fill_hair(orig_bgr, hair_mask)

    # 2. BiSeNet 해제 후 HairFast 로드 및 추론
    _init_hairfast()

    results = []
    for ref in REFERENCE_IMAGES:
        result        = _hair_fast.swap(face_img=source_path, shape_img=ref['path'], color_img=ref['path'], align=True)
        result_tensor = result[0] if isinstance(result, tuple) else result
        result_np     = (result_tensor.permute(1, 2, 0).cpu().clamp(0, 1).numpy() * 255).astype(np.uint8)

        blended = _composite(orig_np, prepped_bgr, result_np)

        filename = f"hair_{uuid.uuid4().hex[:8]}.png"
        out_path = os.path.join(output_dir, filename)
        Image.fromarray(blended).save(out_path)
        results.append({'image_path': out_path, 'name': ref['name']})

    return results
