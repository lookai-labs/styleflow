# -*- coding: utf-8 -*-
import argparse
import os
import numpy as np
import dlib
import tensorflow.compat.v1 as tf
tf.disable_eager_execution()

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

def main():
    parser = argparse.ArgumentParser(description='BeautyGAN: Makeup Transfer')
    parser.add_argument('--source', type=str,
                        default=os.path.join('imgs', 'no_makeup', 'M3.png'),
                        help='path to source (no-makeup) image')
    parser.add_argument('--reference', type=str,
                        default=os.path.join('imgs', 'makeup', 'XMY-136.png'),
                        help='path to reference (makeup) image')
    parser.add_argument('--output', type=str,
                        default='output.png',
                        help='path to save result image')
    args = parser.parse_args()

    landmark_path = os.path.join('models', 'shape_predictor_5_face_landmarks.dat')
    model_dir = 'models'

    print('[1/4] Loading dlib models...')
    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(landmark_path)

    print('[2/4] Loading images and aligning faces...')
    src_img = dlib.load_rgb_image(args.source)
    src_faces = align_face(src_img, detector, sp)
    if len(src_faces) == 0:
        print('Error: No face detected in source image.')
        return

    ref_img = dlib.load_rgb_image(args.reference)
    ref_faces = align_face(ref_img, detector, sp)
    if len(ref_faces) == 0:
        print('Error: No face detected in reference image.')
        return

    src_face = src_faces[0]
    ref_face = ref_faces[0]

    print('[3/4] Loading BeautyGAN model and running inference...')
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    saver = tf.train.import_meta_graph(os.path.join(model_dir, 'model.meta'))
    saver.restore(sess, tf.train.latest_checkpoint(model_dir))
    graph = tf.get_default_graph()

    X = graph.get_tensor_by_name('X:0')
    Y = graph.get_tensor_by_name('Y:0')
    Xs = graph.get_tensor_by_name('generator/xs:0')

    X_img = np.expand_dims(preprocess(src_face), axis=0)
    Y_img = np.expand_dims(preprocess(ref_face), axis=0)

    output = sess.run(Xs, feed_dict={X: X_img, Y: Y_img})
    output_img = postprocess(output[0])

    print('[4/4] Saving result...')
    from PIL import Image
    Image.fromarray(output_img).save(args.output)
    print(f'Done! Result saved to: {args.output}')
    sess.close()

if __name__ == '__main__':
    main()
