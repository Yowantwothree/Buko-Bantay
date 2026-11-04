"""Prototype: coconut leaf disease detector with cited recommendations (TFLite version).

Run:   python app.py
Needs: coconut_leaf_model.tflite and class_names.txt in the same folder as this file.
"""
import os
from pathlib import Path

import gradio as gr
import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image

from recommendations import DISCLAIMER, format_recommendation

APP_DIR = Path(__file__).resolve().parent
MODEL_PATH = APP_DIR / "coconut_leaf_model.tflite"
CLASS_NAMES_PATH = APP_DIR / "class_names.txt"

IMG_SIZE = (256, 256)     # must match training
MIN_CONFIDENCE = 0.80     # below this the app asks for a better photo

CLASS_NAMES = CLASS_NAMES_PATH.read_text().splitlines()

interpreter = Interpreter(model_path=str(MODEL_PATH))
interpreter.allocate_tensors()
INPUT_INDEX = interpreter.get_input_details()[0]["index"]
OUTPUT_INDEX = interpreter.get_output_details()[0]["index"]


def predict(image):
    if image is None:
        return None, "Upload or take a photo of a coconut leaf first."

    # Pixel scaling happens inside the model, so the input stays in the raw 0-255 range.
    arr = np.asarray(image.convert("RGB").resize(IMG_SIZE, Image.BILINEAR), dtype=np.float32)
    interpreter.set_tensor(INPUT_INDEX, arr[np.newaxis])
    interpreter.invoke()
    probs = interpreter.get_tensor(OUTPUT_INDEX)[0]

    scores = {name: float(p) for name, p in zip(CLASS_NAMES, probs)}
    top = int(np.argmax(probs))
    return scores, format_recommendation(CLASS_NAMES[top], float(probs[top]), MIN_CONFIDENCE)


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
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
