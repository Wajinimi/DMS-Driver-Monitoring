# Phase 3 — I amm loading 16-frame clips from disk for TensorFlow training.
import os
import cv2
import numpy as np
import tensorflow as tf

def list_clips(data_root, class_names):
    """
    I'm walking data/train/eat/clip_001/ etc.
    and returning (clip_path, label_index) for every clip.
    """
    clips = []
    for label, class_name in enumerate(class_names):
        class_dir = os.path.join(data_root, class_name)
        if not os.path.isdir(class_dir):
            print(f"Warning: I could not find {class_dir}")
            continue

        for clip_name in os.listdir(class_dir):
            clip_path = os.path.join(class_dir, clip_name)
            if os.path.isdir(clip_path):
                clips.append((clip_path, label))

    return clips



def preprocess_frame(frame, model_size=224, imagenet_mean=None, imagenet_std=None):
    """I'm using the same preprocessing as Phase 2 sliding_buffer."""
    mean = np.array(imagenet_mean or [0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array(imagenet_std or [0.229, 0.224, 0.225], dtype=np.float32)

    resized = cv2.resize(frame, (model_size, model_size), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    pixels = rgb.astype(np.float32) / 255.0
    return (pixels - mean) / std


def load_clip(clip_path, clip_length=16, model_size=224,
              imagenet_mean=None, imagenet_std=None):
    """
    I'm loading one clip folder → numpy array shape (16, 224, 224, 3).
    """
    frame_files = sorted([
        f for f in os.listdir(clip_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    if len(frame_files) == 0:
        raise ValueError(f"I found no images in {clip_path}")

    # I'm picking 16 evenly spaced frames even if the folder has fewer (or more).
    if len(frame_files) >= clip_length:
        selected_files = frame_files[:clip_length]
    else:
        indices = np.linspace(0, len(frame_files) - 1, clip_length, dtype=int)
        selected_files = [frame_files[i] for i in indices]

    frames = []
    for f in selected_files:
        img = cv2.imread(os.path.join(clip_path, f))
        if img is None:
            raise ValueError(f"I could not read {f}")
        frames.append(preprocess_frame(img, model_size, imagenet_mean, imagenet_std))

    return np.stack(frames, axis=0)





def build_tf_dataset(data_root, class_names, clip_length=16, model_size=224,
                     imagenet_mean=None, imagenet_std=None, batch_size=4):
    """
    I'm building a tf.data.Dataset from all clips in data_root.
    """
    clips = list_clips(data_root, class_names)

    def generator():
        for clip_path, label in clips:
            clip = load_clip(clip_path, clip_length, model_size, imagenet_mean, imagenet_std)
            yield clip, label

    output_signature = (
        tf.TensorSpec(shape=(clip_length, model_size, model_size, 3), dtype=tf.float32),
        tf.TensorSpec(shape=(), dtype=tf.int32),
    )

    dataset = tf.data.Dataset.from_generator(generator, output_signature=output_signature)
    dataset = dataset.shuffle(buffer_size=100)
    dataset = dataset.batch(batch_size)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset, len(clips)