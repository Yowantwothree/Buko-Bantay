import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import (ConfusionMatrixDisplay, classification_report,
                             confusion_matrix, f1_score)
from tensorflow.keras import layers

tf.keras.utils.set_random_seed(42)

# =========================================================
# 1. CONFIGURATION
# =========================================================
ROOT_DIR = Path(__file__).resolve().parent
TRAIN_DIR = ROOT_DIR / "train"
VAL_DIR = ROOT_DIR / "validation"
TEST_DIR = ROOT_DIR / "test"

IMG_SIZE = (256, 256)
BATCH_SIZE = 32
HEAD_EPOCHS = 10          # phase 1: train the new classifier head only
FINE_TUNE_EPOCHS = 15     # phase 2: also fine-tune the top of MobileNetV2
FINE_TUNE_LAYERS = 30
SAMPLING_POWER = 0.5      # 0 = natural class frequencies, 1 = fully balanced
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
AUTOTUNE = tf.data.AUTOTUNE

# =========================================================
# 2. FIND FILES AND LABELS (files on disk are never modified)
# =========================================================
class_names = sorted(d.name for d in TRAIN_DIR.iterdir() if d.is_dir())
num_classes = len(class_names)
print("Classes:", class_names)


def key(text):
    """'Gray Leaf Spot' and 'gray_leaf_spot_12' both become 'grayleafspot'."""
    return re.sub(r"[^a-z]", "", text.lower())


class_keys = {key(name): i for i, name in enumerate(class_names)}


def collect_files(folder):
    """Works with class subfolders (folder/Healthy/a.jpg) or a flat folder
    of files named like Healthy12.jpg."""
    paths, labels, unmatched = [], [], []
    for p in sorted(folder.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in IMG_EXTS:
            continue
        name = p.stem if p.parent == folder else p.parent.name
        label = class_keys.get(key(name))
        if label is None:
            unmatched.append(p.name)
        else:
            paths.append(str(p))
            labels.append(label)
    if unmatched:
        print(f"Unmatched files in {folder.name}:", unmatched)
    return np.array(paths), np.array(labels)


train_paths, train_labels = collect_files(TRAIN_DIR)
val_paths, val_labels = collect_files(VAL_DIR)
test_paths, test_labels = collect_files(TEST_DIR)

# =========================================================
# 3. DATA PIPELINES
# =========================================================
def load_image(path, label):
    img = tf.io.decode_image(tf.io.read_file(path), channels=3,
                             expand_animations=False)
    return tf.image.resize(img, IMG_SIZE), label


def eval_dataset(paths, labels):
    return (tf.data.Dataset.from_tensor_slices((paths, labels))
            .map(load_image, num_parallel_calls=AUTOTUNE)
            .batch(BATCH_SIZE).prefetch(AUTOTUNE))


def train_dataset(paths, labels):
    """Draws from each class with probability proportional to count**SAMPLING_POWER,
    so small classes are seen more often (with fresh augmentation each time)."""
    counts = np.bincount(labels, minlength=num_classes)
    probs = counts ** SAMPLING_POWER
    probs = probs / probs.sum()
    print("Natural share :", np.round(counts / counts.sum(), 3))
    print("Sampling share:", np.round(probs, 3))

    per_class = [
        tf.data.Dataset.from_tensor_slices((paths[labels == c], labels[labels == c]))
        .shuffle(counts[c]).repeat()
        for c in range(num_classes)
    ]
    ds = tf.data.Dataset.sample_from_datasets(per_class, weights=probs.tolist())
    ds = (ds.map(load_image, num_parallel_calls=AUTOTUNE)
            .batch(BATCH_SIZE).prefetch(AUTOTUNE))
    return ds, len(labels) // BATCH_SIZE


train_ds, steps_per_epoch = train_dataset(train_paths, train_labels)
val_ds = eval_dataset(val_paths, val_labels)
test_ds = eval_dataset(test_paths, test_labels)

# =========================================================
# 4. MODEL
# =========================================================
# Colour augmentation is kept mild (no hue/saturation shifts) because
# leaf colour is itself a disease signal.
augment = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.1),
    layers.RandomTranslation(0.1, 0.1),
    layers.RandomZoom(0.15),
    layers.RandomBrightness(0.15, value_range=(0, 255)),
    layers.RandomContrast(0.15),
], name="augmentation")

base_model = tf.keras.applications.MobileNetV2(
    input_shape=(*IMG_SIZE, 3), include_top=False, weights="imagenet")
base_model.trainable = False

inputs = layers.Input(shape=(*IMG_SIZE, 3))
x = augment(inputs)  # only active during training
x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.3)(x)
outputs = layers.Dense(num_classes, activation="softmax")(x)
model = tf.keras.Model(inputs, outputs)


def compile_model(learning_rate):
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )


# =========================================================
# 5. TRAINING (monitors macro F1 instead of loss/accuracy)
# =========================================================
class MacroF1(tf.keras.callbacks.Callback):
    """Computes macro F1 on the validation set after every epoch and exposes it
    as 'val_macro_f1' so callbacks listed after it can monitor it."""

    def __init__(self, dataset, y_true):
        super().__init__()
        self.dataset, self.y_true, self.scores = dataset, y_true, []

    def on_epoch_end(self, epoch, logs=None):
        y_pred = np.argmax(self.model.predict(self.dataset, verbose=0), axis=1)
        score = f1_score(self.y_true, y_pred, average="macro")
        self.scores.append(score)
        logs["val_macro_f1"] = score
        print(f" - val_macro_f1: {score:.4f}")


macro_f1 = MacroF1(val_ds, val_labels)


def callbacks(patience):
    return [macro_f1, tf.keras.callbacks.EarlyStopping(
        monitor="val_macro_f1", mode="max", patience=patience,
        restore_best_weights=True)]


# Phase 1: train only the new head
compile_model(1e-3)
head = model.fit(train_ds, steps_per_epoch=steps_per_epoch,
                 validation_data=val_ds, epochs=HEAD_EPOCHS,
                 callbacks=callbacks(patience=4))

# Phase 2: fine-tune the top layers at a low learning rate (BatchNorm stays frozen)
base_model.trainable = True
for layer in base_model.layers[:-FINE_TUNE_LAYERS]:
    layer.trainable = False
for layer in base_model.layers:
    if isinstance(layer, layers.BatchNormalization):
        layer.trainable = False

compile_model(1e-5)
fine = model.fit(train_ds, steps_per_epoch=steps_per_epoch,
                 validation_data=val_ds, epochs=FINE_TUNE_EPOCHS,
                 callbacks=callbacks(patience=5))

model.save(str(ROOT_DIR / "coconut_leaf_model.keras"))
(ROOT_DIR / "class_names.txt").write_text("\n".join(class_names))

# =========================================================
# 6. TRAINING CURVES
# =========================================================
def joined(metric):
    return head.history[metric] + fine.history[metric]


switch = len(head.history["loss"]) - 0.5
fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
for ax, (title, series) in zip(axes, [
    ("Accuracy", [("train", joined("accuracy")), ("val", joined("val_accuracy"))]),
    ("Loss", [("train", joined("loss")), ("val", joined("val_loss"))]),
    ("Validation macro F1", [("val", macro_f1.scores)]),
]):
    for label, values in series:
        ax.plot(values, label=label)
    ax.axvline(switch, color="gray", linestyle="--", label="fine-tuning starts")
    ax.set_title(title)
    ax.set_xlabel("Epoch")
    ax.grid(True)
    ax.legend()
plt.tight_layout()
plt.savefig(ROOT_DIR / "training_curves.png")
plt.close()

# =========================================================
# 7. TEST EVALUATION
# =========================================================
probs = model.predict(test_ds, verbose=0)
preds = np.argmax(probs, axis=1)
test_loss, test_acc = model.evaluate(test_ds, verbose=0)
print(f"\nTest loss: {test_loss:.4f} | Test accuracy: {test_acc:.2%} "
      f"| Images: {len(test_labels)}")

labels_range = list(range(num_classes))
print(classification_report(test_labels, preds, labels=labels_range,
                            target_names=class_names, zero_division=0))

cm = confusion_matrix(test_labels, preds, labels=labels_range)
fig, ax = plt.subplots(figsize=(7, 6))
ConfusionMatrixDisplay(cm, display_labels=class_names).plot(
    ax=ax, xticks_rotation=45, values_format="d", colorbar=False)
plt.title("Confusion matrix (test)")
plt.tight_layout()
plt.savefig(ROOT_DIR / "confusion_matrix.png")
plt.close()

# =========================================================
# 8. MISCLASSIFIED TEST IMAGES (up to 12)
# =========================================================
wrong = np.where(preds != test_labels)[0][:12]
if len(wrong):
    cols = 4
    rows = (len(wrong) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
    axes = np.atleast_1d(axes).ravel()
    for ax, i in zip(axes, wrong):
        img = tf.io.decode_image(tf.io.read_file(test_paths[i]), channels=3,
                                 expand_animations=False).numpy()
        ax.imshow(img)
        ax.set_title(f"Actual: {class_names[test_labels[i]]}\n"
                     f"Predicted: {class_names[preds[i]]} "
                     f"({probs[i].max():.0%})", color="red", fontsize=9)
    for ax in axes:
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(ROOT_DIR / "misclassified.png")
    plt.close()