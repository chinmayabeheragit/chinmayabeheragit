"""Neofetch-style info card -> info-card.svg. Edit ROWS below, then re-run."""
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = os.environ.get("STATIC") == "1"

TITLE = "chinmaya@github"
# (key, value, value colour)
ROWS = [
    ("Role", "Backend Developer", "#79c0ff"),
    ("Stack", "Node.js · NestJS · TypeScript", "#7ee787"),
    ("Data", "PostgreSQL · Redis", "#7ee787"),
    ("Cloud", "AWS · DevOps (growing)", "#ffa657"),
    ("Built", "E-commerce · LMS · HRMS · Trading", "#d2a8ff"),
    ("Focus", "Backend · DevOps · AI/ML", "#79c0ff"),
    ("Where", "Bengaluru, India", "#c9d1d9"),
]
W, LINE, TOP = 490, 26, 84
H = TOP + len(ROWS) * LINE + 28
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def main():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}" font-size="14">',
         '<style>',
         '.l{animation:in .5s ease-out both}',
         '@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}',
         '.k{fill:#f0883e;font-weight:bold}',
         '</style>',
         f'<rect width="{W}" height="{H}" rx="12" fill="#0d1117" stroke="#30363d"/>',
         '<circle cx="22" cy="20" r="6" fill="#ff5f56"/><circle cx="42" cy="20" r="6" fill="#ffbd2e"/><circle cx="62" cy="20" r="6" fill="#27c93f"/>',
         f'<text x="{W // 2}" y="25" fill="#8b949e" font-size="12" text-anchor="middle">neofetch</text>',
         '<line x1="0" y1="38" x2="%d" y2="38" stroke="#30363d"/>' % W]

    def line(i, inner, y):
        style = "" if STATIC else f' style="animation-delay:{300 + i * 220}ms"'
        cls = "" if STATIC else ' class="l"'
        return f'<g{cls}{style}>{inner.replace("{y}", str(y))}</g>'

    o.append(line(0, f'<text x="24" y="{{y}}" fill="#58a6ff" font-weight="bold">{escape(TITLE)}</text>', 64))
    for i, (k, v, colr) in enumerate(ROWS, start=1):
        y = TOP + (i - 1) * LINE + 14
        inner = (f'<text x="24" y="{{y}}"><tspan class="k">{escape(k)}</tspan>'
                 f'<tspan fill="#8b949e">: </tspan><tspan fill="{colr}">{escape(v)}</tspan></text>')
        o.append(line(i, inner, y))
    o.append("</svg>")
    (ROOT / "info-card.svg").write_text("\n".join(o))
    print("wrote info-card.svg")


if __name__ == "__main__":
    main()
