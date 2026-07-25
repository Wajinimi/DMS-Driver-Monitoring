# Phase 3 —I am building the TensorFlow video classifier.
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


def build_video_model(num_classes=5, clip_length=16, height=224, width=224):
    """
    I'm building a 3D CNN that takes (16, 224, 224, 3) and outputs 5 classes.
    Same input shape as Phase 2 clips.
    """
    inputs = keras.Input(shape=(clip_length, height, width, 3), name="video_clip")



        # Block 1 — I'm learning low-level motion + edges.
    x = layers.Conv3D(32, kernel_size=(3, 3, 3), activation="relu", padding="same")(inputs)
    x = layers.MaxPooling3D(pool_size=(1, 2, 2))(x)

    # Block 2 — I'm learning mid-level patterns.
    x = layers.Conv3D(64, kernel_size=(3, 3, 3), activation="relu", padding="same")(x)
    x = layers.MaxPooling3D(pool_size=(2, 2, 2))(x)

    # Block 3 — I'm learning higher-level action features.
    x = layers.Conv3D(128, kernel_size=(3, 3, 3), activation="relu", padding="same")(x)
    x = layers.MaxPooling3D(pool_size=(2, 2, 2))(x)

    # I'm collapsing everything into one feature vector.
    x = layers.GlobalAveragePooling3D()(x)
    x = layers.Dropout(0.5)(x)

    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="dms_video_classifier_v1")
    return model

    