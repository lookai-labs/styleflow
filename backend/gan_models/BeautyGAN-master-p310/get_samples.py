# -*- coding: utf-8 -*-
import os
import numpy as np
import dlib
import tensorflow.compat.v1 as tf
tf.disable_eager_execution()
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

OUTPUT_DIR = 'samples'

PAIRS = [
    {
        'sources':    ['F1', 'F2', 'F3'],
        'references': ['FS1', 'FS2', 'FS3'],
    },
    {
        'sources':    ['M1', 'M2', 'M3'],
        'references': ['MS1', 'MS2', 'MS3'],
    },
]

def align_face(img, detector, sp):
    dets = detector(img, 1)
    objs = dlib.full_object_detections()
    for detection in dets:
        s = sp(img, detection)
        objs.append(s)
    faces = dlib.get_face_chips(img, objs, size=256, padding=0.35)
    return faces

def preprocess(img):
    return img.astype(np.float32) / 127.5 - 1.

def postprocess(img):
    return ((img + 1.) * 127.5).astype(np.uint8)

def load_and_align(path, detector, sp):
    img = np.array(Image.open(path).convert('RGB'))
    faces = align_face(img, detector, sp)
    if len(faces) == 0:
        raise RuntimeError(f'No face detected: {path}')
    return faces[0]

def save_result(src_face, ref_face, output_img, out_path):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].set_title('Source')
    axes[0].imshow(src_face)
    axes[0].axis('off')
    axes[1].set_title('Reference')
    axes[1].imshow(ref_face)
    axes[1].axis('off')
    axes[2].set_title('Result')
    axes[2].imshow(output_img)
    axes[2].axis('off')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print('Loading dlib models...')
    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(os.path.join('models', 'shape_predictor_5_face_landmarks.dat'))

    print('Loading BeautyGAN model...')
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    saver = tf.train.import_meta_graph(os.path.join('models', 'model.meta'))
    saver.restore(sess, tf.train.latest_checkpoint('models'))
    graph = tf.get_default_graph()
    X  = graph.get_tensor_by_name('X:0')
    Y  = graph.get_tensor_by_name('Y:0')
    Xs = graph.get_tensor_by_name('generator/xs:0')

    total = sum(len(p['sources']) * len(p['references']) for p in PAIRS)
    count = 0

    for pair in PAIRS:
        for src_name in pair['sources']:
            src_path = os.path.join('imgs', 'no_makeup', src_name + '.png')
            src_face = load_and_align(src_path, detector, sp)
            X_img = np.expand_dims(preprocess(src_face), axis=0)

            for ref_name in pair['references']:
                count += 1
                ref_path = os.path.join('imgs', 'makeup', ref_name + '.png')
                ref_face = load_and_align(ref_path, detector, sp)
                Y_img = np.expand_dims(preprocess(ref_face), axis=0)

                output = sess.run(Xs, feed_dict={X: X_img, Y: Y_img})
                output_img = postprocess(output[0])

                out_name = f'{src_name}_{ref_name}.png'
                out_path = os.path.join(OUTPUT_DIR, out_name)
                save_result(src_face, ref_face, output_img, out_path)

                print(f'[{count:02d}/{total}] {out_name}')

    sess.close()
    print(f'\nDone! {total} images saved to ./{OUTPUT_DIR}/')

if __name__ == '__main__':
    main()
