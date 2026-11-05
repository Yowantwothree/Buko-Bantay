"""Buko Bantay - coconut leaf health checker (TFLite). Run: python app.py
Needs coconut_leaf_model.tflite and class_names.txt next to this file."""
import os
from pathlib import Path

import gradio as gr
import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image

from i18n import LANGS, NAMES, T, THRESHOLDS, header_html, home_html, result_html, settings_html

APP_DIR = Path(__file__).resolve().parent
IMG_SIZE = (256, 256)  # must match training
CLASS_NAMES = (APP_DIR / "class_names.txt").read_text().splitlines()

interpreter = Interpreter(model_path=str(APP_DIR / "coconut_leaf_model.tflite"))
interpreter.allocate_tensors()
IN_IDX = interpreter.get_input_details()[0]["index"]
OUT_IDX = interpreter.get_output_details()[0]["index"]


def classify(image):
    # Pixel scaling is inside the model, so keep raw 0-255 values.
    arr = np.asarray(image.convert("RGB").resize(IMG_SIZE, Image.BILINEAR), dtype=np.float32)
    interpreter.set_tensor(IN_IDX, arr[np.newaxis])
    interpreter.invoke()
    return interpreter.get_tensor(OUT_IDX)[0].tolist()


def strict_choices(lang):
    return list(zip(T[lang]["strict_opts"], THRESHOLDS))


def pages(name):
    return [gr.update(visible=name == p) for p in ("home", "results", "settings")]


def analyze(image, lang, thr, previous):
    if image is None:
        gr.Warning(T[lang]["no_photo"])
        return [previous, gr.update(), gr.update(), *[gr.update()] * 3]
    probs = classify(image)
    return [(image, probs), image, result_html(lang, thr, probs, CLASS_NAMES), *pages("results")]


def apply_settings(lang, thr, last):
    t = T[lang]
    results = result_html(lang, thr, last[1], CLASS_NAMES) if last else gr.update()
    return [
        header_html(lang), home_html(lang), gr.update(label=t["photo"]), gr.update(value=t["analyze"]),
        gr.update(value=t["nav_home"]), gr.update(value=t["nav_settings"]), gr.update(value=t["again"]),
        results, settings_html(lang),
        gr.update(label=t["language"]),
        gr.update(label=t["strict"], info=t["strict_help"], choices=strict_choices(lang), value=thr),
    ]


CSS = """
.gradio-container, .dark, .dark .gradio-container { color-scheme: light;
  --body-text-color:#3b2f25; --body-text-color-subdued:#7a6a58; --body-background-fill:#faf6ec;
  --background-fill-primary:#ffffff; --background-fill-secondary:#f4efe3; --block-background-fill:#ffffff;
  --block-border-color:#eadfc8; --border-color-primary:#eadfc8; --input-background-fill:#ffffff;
  --block-label-text-color:#5b4a3a; --block-title-text-color:#3b2f25; --block-info-text-color:#7a6a58;
  --checkbox-label-text-color:#3b2f25; --checkbox-label-background-fill:#ffffff;
  --checkbox-label-background-fill-hover:#f4efe3; --checkbox-label-background-fill-selected:#dcebd3;
  --checkbox-label-text-color-selected:#1f4d2b; --checkbox-label-border-color:#eadfc8;
  --checkbox-label-border-color-selected:#2f6b3a; }
.gradio-container label, .gradio-container .block-info, .gradio-container [data-testid="block-label"] { color:#3b2f25 !important; }
:root { --palm:#2f6b3a; --palm-dark:#1f4d2b; --cream:#faf6ec; --husk:#8b5e3c; --leaf:#dcebd3; }
body, .gradio-container { background: var(--cream) !important; }
.gradio-container { max-width: 520px !important; margin: 0 auto !important; padding: 84px 0 96px !important; }
footer { display: none !important; }
#header-wrap { height:0 !important; min-height:0 !important; padding:0 !important; margin:0 !important;
  border:0 !important; background:none !important; overflow:visible !important; }
.appbar { position:fixed; top:0; left:0; right:0; z-index:60; display:flex; gap:12px; align-items:center;
  padding:12px max(16px, calc((100vw - 520px) / 2 + 16px)); padding-top:calc(12px + env(safe-area-inset-top));
  background: linear-gradient(135deg, var(--palm-dark), var(--palm)); border-radius:0 0 24px 24px;
  box-shadow:0 2px 10px rgba(0,0,0,.18); }
.appbar, .appbar * { color:#ffffff !important; }
.appbar .logo { color:#1f4d2b !important; }
.logo { width:44px; height:44px; border-radius:50%; background:var(--cream); color:var(--palm-dark);
  display:flex; align-items:center; justify-content:center; font-weight:800; font-size:22px; border:3px solid var(--husk); }
.brand { font-size:20px; font-weight:800; letter-spacing:.5px; } .tag { font-size:13px; opacity:.9; }
.hero h2, .page-title { color:var(--palm-dark); margin:16px 4px 4px; } .hero p { margin:0 4px 8px; color:#5b4a3a; }
.card, .warn, .disc { background:#fff; border-radius:18px; padding:14px 16px; margin:12px 0; border:1px solid #eadfc8; color:#3b2f25; }
.card h3 { margin:0 0 6px; color:var(--palm-dark); } .card li { margin-bottom:8px; line-height:1.45; }
.chip { display:inline-block; padding:6px 14px; border-radius:999px; font-weight:700; margin-bottom:8px; }
.chip.ok { background:var(--leaf); color:var(--palm-dark); } .chip.bad { background:#fde7c8; color:#9a4a00; }
.chip.unsure { background:#fde2e2; color:#a11d1d; }
.muted { font-size:13px; color:#7a6a58; } .pct { font-size:34px; font-weight:800; color:var(--palm-dark); }
.bar { height:10px; background:#efe7d4; border-radius:99px; overflow:hidden; } .bar span { display:block; height:100%; background:var(--palm); }
.warn { background:#fff4e5; border:2px solid #f2a33a; color:#7a3e00; } .warn p { margin:6px 0 0; }
.disc { background:#f4efe3; font-size:13px; } .disc p { margin:4px 0 0; }
.refs { font-size:12px; word-break:break-word; padding-left:16px; } .ref { color:var(--husk); font-weight:700; }
details summary { cursor:pointer; font-weight:700; color:var(--palm-dark); }
button.primary { background:var(--palm) !important; border:none !important; border-radius:14px !important; font-weight:700 !important; min-height:48px; }
#bottom-nav { position:fixed !important; bottom:0; left:0; right:0; z-index:50; background:#fff; border-top:1px solid #eadfc8;
  padding:6px 8px calc(6px + env(safe-area-inset-bottom)) !important; gap:8px !important; max-width:520px; margin:0 auto; }
#bottom-nav button { flex:1; border-radius:14px !important; background:var(--leaf) !important; color:var(--palm-dark) !important; font-weight:700; }
"""
THEME = gr.themes.Soft(primary_hue="green", secondary_hue="amber", neutral_hue="stone",
                       font=[gr.themes.GoogleFont("Nunito"), "ui-sans-serif", "system-ui", "sans-serif"])
FORCE_LIGHT = """() => {
  const u = new URL(window.location);
  if (u.searchParams.get("__theme") !== "light") { u.searchParams.set("__theme", "light"); window.location.replace(u); }
}"""
STYLE = {"theme": THEME, "css": CSS, "js": FORCE_LIGHT}
V6 = int(gr.__version__.split(".")[0]) >= 6  # Gradio 6 moved theme/css to launch()

with gr.Blocks(title="Buko Bantay", **({} if V6 else STYLE)) as demo:
    last = gr.State(None)  # (image, probabilities) of the latest analysis
    header = gr.HTML(header_html("en"), elem_id="header-wrap")

    with gr.Column(visible=True) as home:
        home_info = gr.HTML(home_html("en"))
        image = gr.Image(type="pil", label=T["en"]["photo"], sources=["upload", "webcam"], height=320)
        analyze_btn = gr.Button(T["en"]["analyze"], variant="primary")

    with gr.Column(visible=False) as results:
        result_img = gr.Image(interactive=False, show_label=False, height=260)
        result_box = gr.HTML()
        again_btn = gr.Button(T["en"]["again"], variant="primary")

    with gr.Column(visible=False) as settings:
        settings_info = gr.HTML(settings_html("en"))
        lang_radio = gr.Radio(LANGS, value="en", label=T["en"]["language"])
        strict_radio = gr.Radio(strict_choices("en"), value=0.80, label=T["en"]["strict"], info=T["en"]["strict_help"])

    with gr.Row(elem_id="bottom-nav"):
        nav_home = gr.Button(T["en"]["nav_home"])
        nav_settings = gr.Button(T["en"]["nav_settings"])

    page_outputs = [home, results, settings]
    analyze_btn.click(analyze, [image, lang_radio, strict_radio, last], [last, result_img, result_box, *page_outputs])
    again_btn.click(lambda: [*pages("home"), None], outputs=[*page_outputs, image])
    nav_home.click(lambda: pages("home"), outputs=page_outputs)
    nav_settings.click(lambda: pages("settings"), outputs=page_outputs)

    ui = [header, home_info, image, analyze_btn, nav_home, nav_settings, again_btn,
          result_box, settings_info, lang_radio, strict_radio]
    for control in (lang_radio, strict_radio):
        control.input(apply_settings, [lang_radio, strict_radio, last], ui)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)),
                pwa=True, **(STYLE if V6 else {}))
