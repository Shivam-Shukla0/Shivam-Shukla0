#!/usr/bin/env python3
"""
Turns a photo into the ASCII portrait (portrait.txt) shown on the left of the
profile card. Run this ONLY when you want to change the photo:

    pip install pillow numpy scipy rembg onnxruntime
    python photo_to_ascii.py my_photo.jpg

Circular avatars (black corners — e.g. saved from LinkedIn / GitHub) are
handled automatically. rembg + scipy give the cleanest result; without them
the script still runs but expects a plain background.

Tuning knobs:
  COLS    characters across (more = more detail)
  DETAIL  local-contrast gain — raise if clothes look like a flat blob
  WEIGHT  global light/dark shape — raise for cleaner bright areas
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

COLS = 96
ASPECT = 1.72          # svg line-height / char-width
BUST = 1.0             # fraction of subject height to keep
DETAIL = 2.8           # local-contrast gain (edges, folds, features)
WEIGHT = 1.10          # global light/dark shape
GAMMA = 0.9
RAMP = "@%#*+=-:. "    # darkest -> lightest


def prep(img):
    """Handle circular avatars: fill corners with bg colour, crop tall."""
    rgb = img.convert("RGB")
    a = np.asarray(rgb).astype(float)
    h, w = a.shape[:2]
    k = max(8, h // 30)
    corners = [a[:k, :k], a[:k, -k:], a[-k:, :k], a[-k:, -k:]]
    if not all(c.max() < 25 for c in corners):
        return rgb                                    # normal photo
    print("[info] circular avatar detected")
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.hypot(yy - h / 2, xx - w / 2)
    ring = (dist > h / 2 - 28) & (dist < h / 2 - 6) & (yy < h * 0.5)
    bg = a[ring].mean(axis=0)
    a[dist > h / 2 - 4] = bg
    mx = int(w * 0.155)
    return Image.fromarray(a.astype(np.uint8)).crop(
        (mx, int(h * 0.02), w - mx, int(h * 0.975)))


def segment(rgb):
    """Person mask via rembg (if installed) + morphological cleanup."""
    try:
        from rembg import remove, new_session
        cut = remove(rgb, session=new_session("u2net_human_seg"))
        alpha = np.asarray(cut)[:, :, 3]
    except ImportError:
        print("[info] rembg not installed — using full frame")
        alpha = np.full(rgb.size[::-1], 255, np.uint8)
    m = alpha > 100
    try:
        import scipy.ndimage as ndi
        m = ndi.binary_opening(m, structure=np.ones((7, 7)))
        lab, n = ndi.label(m)
        if n > 1:
            sizes = ndi.sum(m, lab, range(1, n + 1))
            m = lab == (np.argmax(sizes) + 1)
        m = ndi.binary_fill_holes(ndi.binary_closing(m, np.ones((5, 5))))
    except ImportError:
        print("[info] scipy not installed — skipping mask cleanup")
    return m


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "photo.jpg"
    rgb = prep(Image.open(src))
    m = segment(rgb)

    ys, xs = np.nonzero(m)
    x0, x1, y0 = xs.min(), xs.max(), ys.min()
    y1 = int(y0 + (ys.max() - y0) * BUST)
    pad = 8
    hh, ww = m.shape
    box = (max(0, x0 - pad), max(0, y0 - pad), min(ww, x1 + pad), min(hh, y1))

    rgb = rgb.crop(box)
    m = m[box[1]:box[3], box[0]:box[2]]
    arr = np.asarray(rgb).copy()
    arr[~m] = 0                       # black out the background before tone work
    g = np.asarray(ImageOps.autocontrast(
        Image.fromarray(arr).convert("L"), cutoff=1), dtype=np.int16)
    h, w = g.shape

    # local contrast pulls folds/edges out of flat regions
    blur = np.asarray(Image.fromarray(g.astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(max(2, w // 55))), dtype=np.int16)
    ink = np.clip(150 + (g - blur) * DETAIL + (g - 128) * WEIGHT, 0, 255)
    lo, hi = np.percentile(ink[m], 4), np.percentile(ink[m], 92)
    ink = np.clip((ink - lo) * 255.0 / max(1, hi - lo), 0, 255)
    ink = 255 * (ink / 255) ** GAMMA

    rows = max(1, int(COLS * (h / w) / ASPECT))
    small = np.asarray(Image.fromarray(ink.astype(np.uint8))
                       .resize((COLS, rows), Image.LANCZOS), dtype=float)
    mask = np.asarray(Image.fromarray((m * 255).astype(np.uint8))
                      .resize((COLS, rows), Image.LANCZOS), dtype=float)

    n = len(RAMP) - 1
    filled = [[mask[y, x] > 128 for x in range(COLS)] for y in range(rows)]
    for _ in range(2):                     # drop isolated specks
        nxt = [r[:] for r in filled]
        for y in range(rows):
            for x in range(COLS):
                if filled[y][x]:
                    nb = sum(filled[j][i]
                             for j in range(max(0, y - 1), min(rows, y + 2))
                             for i in range(max(0, x - 1), min(COLS, x + 2))) - 1
                    if nb < 2:
                        nxt[y][x] = False
        filled = nxt

    lines = ["".join(RAMP[round(small[y, x] / 255 * n)] if filled[y][x] else " "
                     for x in range(COLS)).rstrip() for y in range(rows)]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    Path(__file__).parent.joinpath("portrait.txt").write_text(
        "\n".join(lines), encoding="utf-8")
    print(f"wrote portrait.txt  ({COLS} cols x {len(lines)} rows)")


if __name__ == "__main__":
    main()
