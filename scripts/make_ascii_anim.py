"""Daily ASCII dish -> animated terminal panel (ascii-donut.svg).

A different spinning dish each day (donut, pizza, burger, ice-cream, cupcake, samosa, cookie).
usage: python scripts/make_ascii_anim.py [--dish=pizza] [--out=ascii-donut.svg]
Only needs numpy.
"""
import datetime
import sys
from html import escape
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
HANDLE, NAME = "chinmaya@github", "Chinmaya"
W, H = 430, 452
COLS, ROWS, CW, RH = 84, 52, 4.4, 6.8          # glyph grid and cell size
RAMP = ".,-~:;=!*#$@"                           # dim -> bright
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
FRAMES, LOOP = 48, 4.0                          # more frames = smoother (12 fps)
K1, K2, N_PTS = 480.0, 6.0, 120000              # zoom, camera distance, surface samples
GRAD = ("#58a6ff", "#3fb950")
START = datetime.date(2026, 11, 1)              # donut day; the next day is pizza, and so on
LIGHT = np.array([-0.5, -0.45, 0.75]); LIGHT /= np.linalg.norm(LIGHT)
TAU = 2 * np.pi


# ---------- surface sampling helpers: each returns points P, normals N, brightness tweak T ----------
def _stack(parts):
    return tuple(np.concatenate([p[i] for p in parts]) for i in range(3))


def torus(R, r, z, n, rng):
    th, ph = rng.random(n) * TAU, rng.random(n) * TAU
    c = R + r * np.cos(th)
    P = np.stack([c * np.cos(ph), c * np.sin(ph), z + r * np.sin(th)], 1)
    N = np.stack([np.cos(th) * np.cos(ph), np.cos(th) * np.sin(ph), np.sin(th)], 1)
    return P, N, th, ph


def disc_top(rad, z, n, rng, tone, wave=0.0, k=8):
    a = rng.random(n) * TAU
    rr = rad * (1 + wave * np.sin(k * a)) * np.sqrt(rng.random(n))
    x, y = rr * np.cos(a), rr * np.sin(a)
    return np.stack([x, y, np.full(n, z)], 1), np.tile([0.0, 0.0, 1.0], (n, 1)), tone(x, y)


def disc_side(rad, z0, z1, n, rng, tone, wave=0.0, k=8):
    a = rng.random(n) * TAU
    z = z0 + (z1 - z0) * rng.random(n)
    r = rad * (1 + wave * np.sin(k * a))
    return (np.stack([r * np.cos(a), r * np.sin(a), z], 1),
            np.stack([np.cos(a), np.sin(a), np.zeros(n)], 1), tone(a, z))


def ellipsoid(c, rad, n, rng, tone, zmin=-1.0):
    v = rng.normal(size=(n, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True)
    v = v[v[:, 2] >= zmin]
    N = v / np.array(rad); N /= np.linalg.norm(N, axis=1, keepdims=True)
    return v * np.array(rad) + np.array(c), N, tone(v)


def cone(z_apex, z_base, rad, n, rng, tone, t_lo=0.0):
    a = rng.random(n) * TAU
    t = np.sqrt(t_lo ** 2 + (1 - t_lo ** 2) * rng.random(n))
    z = z_apex + (z_base - z_apex) * t
    k = rad / (z_base - z_apex)
    N = np.stack([np.cos(a), np.sin(a), np.full(n, -k)], 1); N /= np.linalg.norm(N, axis=1, keepdims=True)
    return np.stack([rad * t * np.cos(a), rad * t * np.sin(a), z], 1), N, tone(a, z)


def tetra(V, n, rng, tone):
    V = np.array(V, float); cen = V.mean(0); out = []
    for f in [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]:
        A, B, C = V[list(f)]
        u, v = rng.random(n // 4), rng.random(n // 4)
        flip = u + v > 1; u, v = np.where(flip, 1 - u, u), np.where(flip, 1 - v, v)
        b = np.stack([1 - u - v, u, v], 1)
        P = b[:, [0]] * A + b[:, [1]] * B + b[:, [2]] * C
        nr = np.cross(B - A, C - A); nr /= np.linalg.norm(nr)
        if nr @ (A - cen) < 0:
            nr = -nr
        out.append((P, np.tile(nr, (len(P), 1)), tone(b)))
    return _stack(out)


# ---------- the dishes ----------
def donut(n, rng):
    P, N, th, ph = torus(1.0, 0.5, 0.0, n, rng)
    icing = N[:, 2] > -0.15
    sprinkle = (np.sin(9 * ph) * np.sin(7 * th + 3 * ph) > 0.82) & icing
    T = np.where(icing, 0.0, -0.2) + np.where(sprinkle, 0.45, 0.0)
    return P, N, T


def pizza(n, rng):
    pep = [(0.72 * np.cos(k * TAU / 6 + 0.3), 0.72 * np.sin(k * TAU / 6 + 0.3)) for k in range(6)] + [(0.0, 0.0)]

    def top(x, y):
        r, a = np.hypot(x, y), np.arctan2(y, x)
        d = np.min([np.hypot(x - px, y - py) for px, py in pep], axis=0)
        t = np.where(r > 1.22, -0.12, 0.15)
        t = np.where((np.abs(np.sin(4 * a)) < 0.04) & (r < 1.2), -0.4, t)
        return np.where((d < 0.2) & (r < 1.2), -0.38, t)
    return _stack([disc_top(1.45, 0.1, int(n * .75), rng, top),
                   disc_side(1.45, -0.1, 0.1, int(n * .25), rng, lambda a, z: np.full_like(a, -0.2))])


def burger(n, rng):
    flat = lambda v: (lambda *_: np.full_like(_[0], v))
    parts = []
    for rad, z0, z1, tn, w in [(1.35, -0.75, -0.5, 0.05, 0), (1.4, -0.5, -0.25, -0.35, 0),
                               (1.5, -0.25, -0.17, 0.25, 0), (1.5, -0.17, -0.05, 0.1, 0.08)]:
        parts.append(disc_top(rad, z1, int(n * .1), rng, flat(tn), w, 9))
        parts.append(disc_side(rad, z0, z1, int(n * .05), rng, flat(tn), w, 9))
    seeds = lambda v: np.where((np.sin(17 * v[:, 0]) * np.sin(17 * v[:, 1]) > 0.85) & (v[:, 2] > 0.3), 0.35, 0.05)
    parts.append(ellipsoid((0, 0, -0.05), (1.4, 1.4, 0.9), int(n * .6), rng, seeds, zmin=0.0))
    P, N, T = _stack(parts)
    return P * 0.9, N, T


def icecream(n, rng):
    waffle = lambda a, z: 0.14 * np.sign(np.sin(8 * a) * np.sin(10 * z))
    parts = [cone(-1.45, 0.05, 0.75, int(n * .35), rng, waffle),
             ellipsoid((0, 0, 0.5), (0.85, 0.85, 0.8), int(n * .35), rng,
                       lambda v: 0.08 * np.sin(14 * v[:, 0]) * np.sin(14 * v[:, 1]), zmin=-0.2),
             ellipsoid((0, 0, 1.45), (0.2, 0.2, 0.2), int(n * .08), rng, lambda v: np.full(len(v), 0.45))]
    P, N, th, ph = torus(0.8, 0.13, 0.12, int(n * .22), rng)
    parts.append((P, N, 0.15 * np.sign(np.sin(18 * ph))))
    P, N, T = _stack(parts)
    P[:, 2] -= 0.07
    return P, N, T


def cupcake(n, rng):
    ridge = lambda a, z: 0.15 * np.sign(np.sin(14 * a)) - 0.05
    parts = [cone(-3.0, 0.0, 1.0, int(n * .3), rng, ridge, t_lo=0.7)]
    for R, r, z in [(0.9, 0.32, 0.15), (0.62, 0.28, 0.5), (0.34, 0.24, 0.82)]:
        P, N, th, ph = torus(R, r, z, int(n * .17), rng)
        parts.append((P, N, 0.12 * np.sin(5 * ph + 2 * th)))
    parts.append(ellipsoid((0, 0, 1.02), (0.28, 0.28, 0.3), int(n * .05), rng, lambda v: np.full(len(v), 0.1), zmin=0.0))
    parts.append(ellipsoid((0, 0, 1.38), (0.18, 0.18, 0.18), int(n * .04), rng, lambda v: np.full(len(v), 0.45)))
    P, N, T = _stack(parts)
    P[:, 2] -= 0.33
    return P, N, T


def samosa(n, rng):
    V = [(0, 0, 1.5), (0, 1.414, -0.5), (-1.2247, -0.707, -0.5), (1.2247, -0.707, -0.5)]
    def tone(b):
        edge = b.min(1) < 0.07
        return np.where(edge, 0.3, -0.05 + 0.15 * np.sin(23 * b[:, 0]) * np.sin(19 * b[:, 1]))
    return tetra(V, n, rng, tone)


def cookie(n, rng):
    chips = [(0.3, 0.2), (-0.5, 0.5), (-0.2, -0.5), (0.7, -0.4), (-0.9, -0.1), (0.2, 0.8), (-0.6, -0.8), (0.45, -0.95), (0.0, -0.1)]
    bx, by, br, rad = 1.25, 0.55, 0.55, 1.45

    def top(x, y):
        d = np.min([np.hypot(x - cx, y - cy) for cx, cy in chips], axis=0)
        return np.where(d < 0.15, -0.4, 0.05 + 0.08 * np.sin(13 * x) * np.sin(11 * y))
    P, N, T = _stack([disc_top(rad, 0.15, int(n * .7), rng, top),
                      disc_side(rad, -0.15, 0.15, int(n * .2), rng, lambda a, z: np.full_like(a, -0.15))])
    keep = np.hypot(P[:, 0] - bx, P[:, 1] - by) >= br                     # take a bite out of it
    a = rng.random(int(n * .1)) * TAU
    wx, wy = bx + br * np.cos(a), by + br * np.sin(a)
    inside = np.hypot(wx, wy) < rad
    a, wx, wy = a[inside], wx[inside], wy[inside]
    wall = (np.stack([wx, wy, -0.15 + 0.3 * rng.random(len(a))], 1),
            np.stack([-np.cos(a), -np.sin(a), np.zeros(len(a))], 1), np.full(len(a), -0.15))
    return _stack([(P[keep], N[keep], T[keep]), wall])


DISHES = [("donut", donut), ("pizza", pizza), ("burger", burger), ("ice-cream", icecream),
          ("cupcake", cupcake), ("samosa", samosa), ("cookie", cookie)]


# ---------- rendering ----------
def render(P, N, T):
    frames = []
    for i in range(FRAMES):
        t = i / FRAMES
        psi, e = TAU * t, 0.9 + 0.18 * np.sin(TAU * t)                    # one full turn per loop + gentle tilt
        cp, sp, ce, se = np.cos(psi), np.sin(psi), np.cos(e), np.sin(e)
        x1, y1, z1 = P[:, 0] * cp - P[:, 1] * sp, P[:, 0] * sp + P[:, 1] * cp, P[:, 2]
        nx, ny, nz = N[:, 0] * cp - N[:, 1] * sp, N[:, 0] * sp + N[:, 1] * cp, N[:, 2]
        vis = (-ny * ce + nz * se) > -0.05                                 # drop faces turned away
        depth = K2 + y1 * ce - z1 * se
        xp, yp = COLS * CW / 2 + K1 * x1 / depth, ROWS * RH / 2 - K1 * (y1 * se + z1 * ce) / depth
        col, row = np.floor(xp / CW).astype(int), np.floor(yp / RH).astype(int)
        lum = 0.14 + 0.86 * np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1) + T
        ok = vis & (col >= 0) & (col < COLS) & (row >= 0) & (row < ROWS)
        c, r, d, l = col[ok], row[ok], depth[ok], lum[ok]
        order = np.argsort(-d)                                             # far -> near, nearest wins
        grid = np.full((ROWS, COLS), -1)
        grid[r[order], c[order]] = np.clip((l[order] * len(RAMP)).astype(int), 0, len(RAMP) - 1)
        frames.append(["".join(RAMP[v] if v >= 0 else " " for v in row_) for row_ in grid])
    return frames


def build(frames, dish):
    ox = (W - COLS * CW) / 2
    oy = 28 + (H - 58 - ROWS * RH) / 2
    pct = 100 / len(frames)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         '<style>.cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}'
         f'.f{{opacity:0;animation:s {LOOP}s step-end infinite}}'
         f'@keyframes s{{0%{{opacity:1}}{pct:.3f}%{{opacity:0}}100%{{opacity:0}}}}</style>',
         f'<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{ox:.1f}" y1="0" x2="{ox + COLS * CW:.1f}" y2="0">'
         f'<stop offset="0" stop-color="{GRAD[0]}"/><stop offset="1" stop-color="{GRAD[1]}"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
         '<circle cx="14" cy="14" r="3.5" fill="#ff5f56"/><circle cx="26" cy="14" r="3.5" fill="#ffbd2e"/><circle cx="38" cy="14" r="3.5" fill="#27c93f"/>',
         f'<text x="{W//2}" y="17" fill="#6e7681" font-size="9" text-anchor="middle">{HANDLE}: ~$ ./{dish}.sh</text>',
         f'<line x1="0" y1="28" x2="{W}" y2="28" stroke="#21262d"/>',
         f'<line x1="0" y1="{H-30}" x2="{W}" y2="{H-30}" stroke="#21262d"/>']
    for i, rows in enumerate(frames):
        first = "opacity:1;" if i == 0 else ""
        o.append(f'<g class="f" style="{first}animation-delay:{i * LOOP / len(frames):.3f}s" fill="url(#g)" '
                 f'font-size="{CW / 0.6:.2f}" xml:space="preserve">')
        for r, row in enumerate(rows):
            s = row.strip(" ")
            if s:
                x = ox + (len(row) - len(row.lstrip(" "))) * CW
                o.append(f'<text x="{x:.1f}" y="{oy + r * RH + RH * 0.85:.1f}" textLength="{len(s) * CW:.1f}">{escape(s)}</text>')
        o.append('</g>')
    py = H - 12
    o.append(f'<text x="14" y="{py}" font-size="8" fill="#6e7681">{HANDLE}:~$ whoami</text>')
    o.append(f'<text x="{14 + 26 * 4.8:.1f}" y="{py}" font-size="8" font-weight="bold" fill="#e6edf3">{escape(NAME)}</text>')
    o.append(f'<rect class="cur" x="{14 + 26 * 4.8 + (len(NAME) + 1) * 4.9:.1f}" y="{py - 8}" width="5" height="9" fill="#e6edf3"/>')
    o.append(f'<text x="{W - 14}" y="{py}" font-size="8" fill="#6e7681" text-anchor="end">today\'s special: {dish}</text>')
    o.append('</svg>')
    return "\n".join(o)


if __name__ == "__main__":
    out, dish = ROOT / "ascii-donut.svg", None
    for a in sys.argv[1:]:
        if a.startswith("--out="):
            out = Path(a.split("=", 1)[1])
        elif a.startswith("--dish="):
            dish = a.split("=", 1)[1]
    names = [d[0] for d in DISHES]
    if dish is None:
        ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        dish = names[(datetime.datetime.now(ist).date() - START).days % len(names)]
    if dish not in names:
        raise SystemExit(f"unknown dish '{dish}', choose from: {', '.join(names)}")
    P, N, T = dict(DISHES)[dish](N_PTS, np.random.default_rng(42))
    out.write_text(build(render(P, N, T), dish))
    print(f"wrote {out} - today's special: {dish} ({out.stat().st_size // 1024} KB)")