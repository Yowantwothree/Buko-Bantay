"""Prototype: coconut leaf disease detector with cited recommendations.

Run:   python app.py
Needs: coconut_leaf_model.keras and class_names.txt (both written by the training
       script) in the same folder as this file.
"""
from pathlib import Path

import gradio as gr
import numpy as np
import tensorflow as tf

from recommendations import DISCLAIMER, format_recommendation

APP_DIR = Path(__file__).resolve().parent
MODEL_PATH = APP_DIR / "coconut_leaf_model.keras"
CLASS_NAMES_PATH = APP_DIR / "class_names.txt"

IMG_SIZE = (256, 256)     # must match training
MIN_CONFIDENCE = 0.80     # below this the app asks for a better photo

model = tf.keras.models.load_model(MODEL_PATH)
CLASS_NAMES = CLASS_NAMES_PATH.read_text().splitlines()


def predict(image):
    if image is None:
        return None, "Upload or take a photo of a coconut leaf first."

    # Same resize as training. Pixel scaling is done inside the model,
    # so the input stays in the raw 0-255 range.
    resized = tf.image.resize(np.asarray(image.convert("RGB")), IMG_SIZE).numpy()
    probs = model.predict(resized[np.newaxis].astype("float32"), verbose=0)[0]

    scores = {name: float(p) for name, p in zip(CLASS_NAMES, probs)}
    top = int(np.argmax(probs))
    advice = format_recommendation(CLASS_NAMES[top], float(probs[top]), MIN_CONFIDENCE)
    return scores, advice


ABOUT = (
    "**About this prototype.** It was tested on 132 leaf photos: 97.7% overall "
    "accuracy, but it missed 3 of 9 healthy leaves. If it reports a disease on a leaf "
    "that looks healthy, double-check before treating. " + DISCLAIMER
)

with gr.Blocks(title="Coconut Leaf Disease Detector") as demo:
    gr.Markdown("# Coconut Leaf Disease Detector\n"
                "Upload or take a clear photo of a single coconut leaf.")
    with gr.Row():
        with gr.Column():
            image = gr.Image(type="pil", label="Leaf photo", sources=["upload", "webcam"])
            button = gr.Button("Analyze", variant="primary")
        with gr.Column():
            label = gr.Label(num_top_classes=len(CLASS_NAMES), label="Prediction")
    advice = gr.Markdown()
    gr.Markdown(ABOUT)

    button.click(predict, inputs=image, outputs=[label, advice])

if __name__ == "__main__":
    # 0.0.0.0 lets a phone on the same Wi-Fi open the app at http://<computer-ip>:7860
    demo.launch(server_name="127.0.0.1", server_port=7860)
