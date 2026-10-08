"""data/contributions.json -> contrib-heatmap.svg (animated once, then frozen)"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BOX, GAP, LEFT, TOP = 12, 3, 38, 58
STEP = BOX + GAP
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def level(d):
    """GitHub gives levels 0-4; promote the busiest days to the neon level 5."""
    return 5 if d["level"] == 4 and d["count"] >= 8 else d["level"]


def main():
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    days, st = data["days"], data["stats"]
    first = date.fromisoformat(days[0]["date"])
    # GitHub weeks start on Sunday; column = weeks since the first day's Sunday
    start_sun = first.toordinal() - (first.weekday() + 1) % 7
    cells, months = [], {}
    for d in days:
        dt = date.fromisoformat(d["date"])
        col = (dt.toordinal() - start_sun) // 7
        row = (dt.weekday() + 1) % 7
        cells.append((col, row, d))
        if row == 0 and dt.day <= 7 and dt.strftime("%b") not in months.values():
            months[col] = dt.strftime("%b")
    cols = max(c for c, _, _ in cells) + 1
    width = LEFT + cols * STEP + 24
    height = TOP + 7 * STEP + 62

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{FONT}">',
         '<style>',
         '.c{transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.2,.8,.2,1) both}',
         '@keyframes pop{from{opacity:0;transform:translateY(-8px) scale(.6)}to{opacity:1;transform:none}}',
         '.t{fill:#8b949e;font-size:11px}.h{fill:#c9d1d9;font-size:13px}',
         '</style>',
         f'<rect width="{width}" height="{height}" rx="12" fill="#0d1117" stroke="#30363d"/>',
         f'<text x="{LEFT}" y="28" class="h">$ ./contributions.sh</text>']
    for col, name in months.items():
        o.append(f'<text x="{LEFT + col * STEP}" y="{TOP - 8}" class="t">{name}</text>')
    for row, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(f'<text x="8" y="{TOP + row * STEP + 10}" class="t">{lab}</text>')
    for col, row, d in cells:
        delay = (col + row) * 18
        tip = f'{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {d["date"]}'
        o.append(f'<rect class="c" style="animation-delay:{delay}ms" x="{LEFT + col * STEP}" y="{TOP + row * STEP}" '
                 f'width="{BOX}" height="{BOX}" rx="3" fill="{PALETTE[level(d)]}"><title>{tip}</title></rect>')
    fy = TOP + 7 * STEP + 22
    o.append(f'<text x="{LEFT}" y="{fy}" class="t">{st["total"]:,} contributions in the last year · '
             f'current streak {st["current_streak"]}d · longest {st["longest_streak"]}d</text>')
    lx = width - 24 - (len(PALETTE) * STEP) - 64
    o.append(f'<text x="{lx - 30}" y="{fy}" class="t">Less</text>')
    for i, colr in enumerate(PALETTE):
        o.append(f'<rect x="{lx + i * STEP}" y="{fy - 10}" width="{BOX}" height="{BOX}" rx="3" fill="{colr}"/>')
    o.append(f'<text x="{lx + len(PALETTE) * STEP + 4}" y="{fy}" class="t">More</text>')
    o.append("</svg>")
    (ROOT / "contrib-heatmap.svg").write_text("\n".join(o))
    print("wrote contrib-heatmap.svg", width, "x", height)


if __name__ == "__main__":
    main()
