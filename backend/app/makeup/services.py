import os
import uuid
import threading
from collections import defaultdict
from pathlib import Path

import numpy as np
import dlib
import cv2


def _patch_protobuf_for_mediapipe() -> None:
    """protobuf 4.x+ 에서 제거된 GetPrototype 을 mediapipe 0.10.9 가 요구한다.
    GetMessageClass 로 위임하는 메서드를 동적으로 추가한다."""
    try:
        from google.protobuf import message_factory as _mf
        get_class = getattr(_mf, "GetMessageClass", None)
        if get_class is None:
            return

        from google.protobuf import symbol_database as _sdb
        if not hasattr(_sdb.Default().__class__, "GetPrototype"):
            _sdb.Default().__class__.GetPrototype = lambda self, desc: get_class(desc)

        if not hasattr(_mf.MessageFactory, "GetPrototype"):
            _mf.MessageFactory.GetPrototype = lambda self, desc: get_class(desc)
    except Exception:
        pass


_patch_protobuf_for_mediapipe()

import mediapipe as mp
import tensorflow.compat.v1 as tf
tf.disable_eager_execution()
from PIL import Image

_lock = threading.Lock()

BEAUTYGAN_DIR = Path(__file__).resolve().parent.parent.parent / 'gan_models' / 'BeautyGAN-master-p310'
MODEL_DIR = str(BEAUTYGAN_DIR / 'models')
LANDMARK_PATH = str(BEAUTYGAN_DIR / 'models' / 'shape_predictor_5_face_landmarks.dat')

REFERENCE_IMAGES = [
    {'path': str(BEAUTYGAN_DIR / 'imgs' / 'makeup' / 'MS1.png'), 'name': '웜 코랄 메이크업'},
    {'path': str(BEAUTYGAN_DIR / 'imgs' / 'makeup' / 'MS2.png'), 'name': '소프트 뉴트럴'},
    {'path': str(BEAUTYGAN_DIR / 'imgs' / 'makeup' / 'MS3.png'), 'name': '로즈 글로우'},
]

_detector = None
_sp = None
_face_mesh = None
_OVAL_IDX = None


def _get_dlib():
    global _detector, _sp
    if _detector is None:
        _detector = dlib.get_frontal_face_detector()
        _sp = dlib.shape_predictor(LANDMARK_PATH)
    return _detector, _sp


def _build_oval_order(connections):
    adj = defaultdict(set)
    for a, b in connections:
        adj[a].add(b)
        adj[b].add(a)
    start = next(iter(connections))[0]
    ordered = [start]
    prev, cur = None, start
    while True:
        nxt = (adj[cur] - ({prev} if prev is not None else set())) - {start}
        if not nxt:
            break
        n = next(iter(nxt))
        ordered.append(n)
        prev, cur = cur, n
        if cur == start:
            break
    return ordered


def _init_mediapipe():
    global _face_mesh, _OVAL_IDX
    if _face_mesh is None:
        _face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
        )
        _OVAL_IDX = _build_oval_order(mp.solutions.face_mesh.FACEMESH_FACE_OVAL)


def get_face_mask_on_original(img_np):
    _init_mediapipe()
    h, w = img_np.shape[:2]
    res = _face_mesh.process(img_np)

    if not res.multi_face_landmarks:
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(mask, (w // 2, h // 2),
                    (int(w * 0.35), int(h * 0.42)), 0, 0, 360, 255, -1)
        return mask

    lm = res.multi_face_landmarks[0]
    pts = np.array(
        [[int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)] for i in _OVAL_IDX],
        dtype=np.int32,
    )
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [pts], 255)
    return mask


def get_face_transform(img, detector, sp, size=256, padding=0.35):
    dets = detector(img, 1)
    if len(dets) == 0:
        return []

    objs = dlib.full_object_detections()
    for det in dets:
        objs.append(sp(img, det))

    chips = dlib.get_face_chips(img, objs, size=size, padding=padding)

    results = []
    for i, chip in enumerate(chips):
        chip_np = np.array(chip)

        lm_orig = objs[i]
        src_pts = np.array(
            [[lm_orig.part(j).x, lm_orig.part(j).y] for j in range(5)],
            dtype=np.float64,
        )

        chip_dets = detector(chip, 1)
        if len(chip_dets) > 0:
            lm_chip = sp(chip, chip_dets[0])
            dst_pts = np.array(
                [[lm_chip.part(j).x, lm_chip.part(j).y] for j in range(5)],
                dtype=np.float64,
            )
        else:
            raw = np.array([[0.1875, 0.2], [0.3125, 0.2], [0.6875, 0.2], [0.8125, 0.2], [0.5, 0.5]])
            dst_pts = ((raw - 0.5) / (1 + 2 * padding) + 0.5) * size

        M, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.LMEDS)
        M_inv = cv2.invertAffineTransform(M)
        results.append((chip_np, M_inv))

    return results


def estimate_chip_delta(src_face, makeup_face):
    src_mean = src_face.astype(np.float32).mean(axis=(0, 1))
    mkup_mean = makeup_face.astype(np.float32).mean(axis=(0, 1))
    return mkup_mean - src_mean


def blend_face_to_original(original_img, makeup_face, M_inv, face_mask_orig, src_face):
    h, w = original_img.shape[:2]

    warped_face = cv2.warpAffine(
        makeup_face, M_inv, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=0,
    )

    chip_valid = cv2.warpAffine(
        np.ones((256, 256), dtype=np.uint8) * 255,
        M_inv, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=0,
    )
    _, chip_valid = cv2.threshold(chip_valid, 128, 255, cv2.THRESH_BINARY)

    delta = estimate_chip_delta(src_face, makeup_face)

    _, _, bw, bh = cv2.boundingRect(face_mask_orig)
    fade_distance = max(bw, bh) * 0.8

    outside_mask = cv2.bitwise_not(face_mask_orig)
    dist = cv2.distanceTransform(outside_mask, cv2.DIST_L2, 5)
    fade_weight = np.clip(1.0 - dist / fade_distance, 0.0, 1.0)

    base = original_img.astype(np.float32)
    for c in range(3):
        base[:, :, c] = np.clip(base[:, :, c] + delta[c] * fade_weight, 0, 255)
    base_adjusted = base.astype(np.uint8)

    feathered = cv2.GaussianBlur(face_mask_orig, (51, 51), 0).astype(np.float32)
    feathered[chip_valid == 0] = 0
    alpha = (feathered / 255.0)[:, :, np.newaxis]
    return (warped_face * alpha + base_adjusted * (1 - alpha)).astype(np.uint8)


def release_tf_memory():
    import gc
    tf.reset_default_graph()
    gc.collect()


def run_makeup(source_path: str, output_dir: str) -> list:
    with _lock:
        return _run_makeup_inner(source_path, output_dir)


def _run_makeup_inner(source_path: str, output_dir: str) -> list:
    detector, sp = _get_dlib()

    src_img = dlib.load_rgb_image(source_path)
    src_results = get_face_transform(src_img, detector, sp)
    if not src_results:
        raise ValueError("소스 이미지에서 얼굴을 찾을 수 없습니다.")
    src_face, src_M_inv = src_results[0]

    src_img_np = np.array(src_img)
    face_mask = get_face_mask_on_original(src_img_np)

    tf.reset_default_graph()
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    saver = tf.train.import_meta_graph(os.path.join(MODEL_DIR, 'model.meta'))
    saver.restore(sess, tf.train.latest_checkpoint(MODEL_DIR))
    graph = tf.get_default_graph()

    X = graph.get_tensor_by_name('X:0')
    Y = graph.get_tensor_by_name('Y:0')
    Xs = graph.get_tensor_by_name('generator/xs:0')

    X_img = np.expand_dims(src_face.astype(np.float32) / 127.5 - 1., axis=0)

    os.makedirs(output_dir, exist_ok=True)
    results = []

    for ref in REFERENCE_IMAGES:
        ref_img = dlib.load_rgb_image(ref['path'])
        ref_results = get_face_transform(ref_img, detector, sp)
        if not ref_results:
            continue
        ref_face, _ = ref_results[0]
        Y_img = np.expand_dims(ref_face.astype(np.float32) / 127.5 - 1., axis=0)

        output = sess.run(Xs, feed_dict={X: X_img, Y: Y_img})
        makeup_face = ((output[0] + 1.) * 127.5).astype(np.uint8)

        result_full = blend_face_to_original(src_img_np, makeup_face, src_M_inv, face_mask, src_face)

        filename = f"makeup_{uuid.uuid4().hex[:8]}.png"
        out_path = os.path.join(output_dir, filename)
        Image.fromarray(result_full).save(out_path)
        results.append({'image_path': out_path, 'name': ref['name']})

    sess.close()
    return results
