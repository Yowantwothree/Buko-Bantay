"""Simple photo-quality gate (FR-004): blur and brightness checks, no extra libraries."""
import numpy as np
from PIL import ImageOps

# TUNE THESE on your own photos: print the numbers with `python quality.py photo.jpg`
BLUR_MIN = 60.0     # Laplacian variance below this = blurry
DARK_MAX = 50       # mean gray level below this = too dark
BRIGHT_MIN = 235    # mean gray level above this = washed out


def measure(img):
    g = np.asarray(ImageOps.exif_transpose(img).convert("L").resize((256, 256)), dtype=np.float32)
    lap = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(lap.var()), float(g.mean())


def check_quality(img):
    """Return (ok, reason) where reason is 'ok', 'blurry', 'dark' or 'bright'."""
    sharp, mean = measure(img)
    if sharp < BLUR_MIN:
        return False, "blurry"
    if mean < DARK_MAX:
        return False, "dark"
    if mean > BRIGHT_MIN:
        return False, "bright"
    return True, "ok"


if __name__ == "__main__":
    import sys
    from PIL import Image
    for path in sys.argv[1:]:
        s, m = measure(Image.open(path))
        print(f"{path}: sharpness={s:.1f} brightness={m:.1f} -> {check_quality(Image.open(path))}")