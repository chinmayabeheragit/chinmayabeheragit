"""Photo -> animated monochrome ASCII portrait terminal panel (ascii-portrait.svg).

usage: python scripts/make_ascii_svg.py my-photo.jpg [--no-rembg] [--crop=x0,y0,x1,y1]
Run it locally only when you change your photo (needs pillow, numpy, opencv-python, rembg).
"""
import os
import sys
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
HANDLE, NAME = "chinmaya@github", "Chinmaya"
W, H = 430, 452
COLS, ROWS, CW, RH = 96, 60, 4.0, 6.2          # glyph grid and cell size
RAMP = " .`:-=+*cs#%@"                        # bright (sparse) -> dark (dense)
FILL, FONT = "#c9d1d9", "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def prep(path, use_rembg=True, crop=None):
    img = Image.open(path).convert("RGB")
    if crop:  # (x0, y0, x1, y1) as fractions of the photo, e.g. 0.2,0.1,0.8,0.7
        w, h = img.size
        img = img.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    if max(img.size) < 800:  # small photos give the cut-out model more to work with
        k = 800 / max(img.size)
        img = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
    img.thumbnail((1200, 1200))
    mask = None
    if use_rembg:
        try:
            from rembg import new_session, remove
            # small portrait model (~170 MB, downloaded once); set REMBG_MODEL=u2netp for a ~4 MB one
            session = new_session(os.environ.get("REMBG_MODEL", "u2net_human_seg"))
            cut = remove(img, session=session)      # RGBA, background removed
            mask = np.array(cut)[:, :, 3] > 40
        except Exception as e:                      # model download blocked etc.
            print("rembg skipped:", e)
    gray = np.array(img.convert("L"))
    try:
        import cv2
        gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
    except Exception:
        pass
    if mask is not None:
        gray = np.where(mask, gray, 255).astype(np.uint8)   # background -> white -> spaces
        ys, xs = np.where(mask)
        pad = 12
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, gray.shape[0])
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, gray.shape[1])
        gray = gray[y0:y1, x0:x1]
    # pad to the aspect ratio of the glyph grid, then resize to one pixel per glyph
    target = (COLS * CW) / (ROWS * RH)
    h, w = gray.shape
    if w / h < target:
        nw = int(h * target); canvas = np.full((h, nw), 255, np.uint8)
        canvas[:, (nw - w) // 2:(nw - w) // 2 + w] = gray
    else:
        nh = int(w / target); canvas = np.full((nh, w), 255, np.uint8)
        canvas[(nh - h) // 2:(nh - h) // 2 + h, :] = gray
    return np.array(Image.fromarray(canvas).resize((COLS, ROWS), Image.LANCZOS))


def to_rows(px):
    n = len(RAMP)
    return ["".join(RAMP[min(n - 1, int((255 - int(v)) / 256 * n))] for v in row) for row in px]


def build(rows):
    ox = (W - COLS * CW) / 2
    oy = 40
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         '<style>.cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}'
         '.p{opacity:0;animation:show .01s linear forwards}@keyframes show{to{opacity:1}}</style>',
         f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
         '<circle cx="14" cy="14" r="3.5" fill="#ff5f56"/><circle cx="26" cy="14" r="3.5" fill="#ffbd2e"/><circle cx="38" cy="14" r="3.5" fill="#27c93f"/>',
         f'<text x="{W//2}" y="17" fill="#6e7681" font-size="9" text-anchor="middle">{HANDLE}: ~$ ./portrait.sh</text>',
         f'<line x1="0" y1="28" x2="{W}" y2="28" stroke="#21262d"/>',
         f'<line x1="0" y1="{H-30}" x2="{W}" y2="{H-30}" stroke="#21262d"/>', '<defs>']
    step, dur = 0.055, 0.35
    texts = []
    for i, row in enumerate(rows):
        stripped = row.strip(" ")
        if not stripped:
            continue
        lead = len(row) - len(row.lstrip(" "))
        y = oy + i * RH
        x = ox + lead * CW
        o.append(f'<clipPath id="r{i}"><rect x="{ox:.1f}" y="{y:.1f}" width="0" height="{RH + 1:.1f}">'
                 f'<animate attributeName="width" from="0" to="{COLS * CW:.1f}" begin="{0.3 + i * step:.2f}s" dur="{dur}s" fill="freeze"/></rect></clipPath>')
        texts.append(f'<text clip-path="url(#r{i})" x="{x:.1f}" y="{y + RH * 0.85:.1f}" font-size="{CW / 0.6:.2f}" '
                     f'fill="{FILL}" textLength="{len(stripped) * CW:.1f}" lengthAdjust="spacing" xml:space="preserve">{escape(stripped)}</text>')
    o.append('</defs>')
    o += texts
    t = 0.3 + len(rows) * step + dur
    py = H - 12
    o.append(f'<text x="14" y="{py}" font-size="8" fill="#6e7681">{HANDLE}:~$ whoami</text>')
    o.append(f'<text class="p" style="animation-delay:{t:.2f}s" x="{14 + 26 * 4.8:.1f}" y="{py}" font-size="8" font-weight="bold" fill="#e6edf3">{escape(NAME)}</text>')
    o.append(f'<rect class="cur" x="{14 + 26 * 4.8 + (len(NAME) + 1) * 4.9:.1f}" y="{py - 8}" width="5" height="9" fill="#e6edf3"/>')
    o.append('</svg>')
    return "\n".join(o)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    crop = None
    for a in sys.argv[2:]:
        if a.startswith("--crop="):
            crop = [float(v) for v in a.split("=")[1].split(",")]
    rows = to_rows(prep(sys.argv[1], "--no-rembg" not in sys.argv, crop))
    (ROOT / "ascii-portrait.svg").write_text(build(rows))
    print("wrote ascii-portrait.svg")
