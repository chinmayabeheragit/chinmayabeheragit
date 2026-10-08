"""data/contributions.json -> stats.svg (terminal-style stats panel)"""
import json
from collections import OrderedDict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HANDLE = "chinmaya@github"
W, H = 430, 452
GREEN, WHITE, GRAY, DIM = "#3fb950", "#e6edf3", "#8b949e", "#6e7681"
BAR = "#26c452"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def fmt(d):  # "May 10"
    return d.strftime("%b ") + str(d.day)


def streaks(days):
    """Return (current, longest) as (length, start_date, end_date)."""
    best = cur = (0, None, None)
    run_start, run_len = None, 0
    runs = []
    for d in days:
        dt = date.fromisoformat(d["date"])
        if d["count"] > 0:
            if run_len == 0:
                run_start = dt
            run_len += 1
            last = dt
        elif run_len:
            runs.append((run_len, run_start, last)); run_len = 0
    if run_len:
        runs.append((run_len, run_start, last))
    longest = max(runs, key=lambda r: r[0]) if runs else (0, None, None)
    current = (0, None, None)
    if runs:
        end = date.fromisoformat(days[-1]["date"])
        r = runs[-1]
        if (end - r[2]).days <= 1:  # today may still be empty
            current = r
    return current, longest


def rng(s):
    return f"{fmt(s[1])} – {fmt(s[2])}" if s[0] else "no streak yet"


def main():
    days = json.loads((ROOT / "data" / "contributions.json").read_text())["days"]
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    # the live calendar includes future empty cells in the last week; ignore them
    today = date.today()
    past = [d for d in days if date.fromisoformat(d["date"]) <= today] or days
    active_pct = round(100 * active / len(past)) if past else 0
    cur, lng = streaks(past)
    best = max(past, key=lambda d: d["count"])
    avg = total / active if active else 0
    months = OrderedDict()
    for d in past:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    mvals = list(months.items())[-13:]

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         '<style>',
         '.c{animation:in .6s ease-out both}',
         '@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}',
         '.b{transform-box:fill-box;transform-origin:bottom;animation:grow .8s cubic-bezier(.2,.8,.2,1) both}',
         '@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}',
         '.lab{fill:%s;font-size:11px}.big{font-size:30px;font-weight:bold}.sub{fill:%s;font-size:10px}.unit{fill:%s;font-size:13px;font-weight:normal}' % (GRAY, DIM, GRAY),
         '</style>',
         f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
         '<circle cx="14" cy="14" r="3.5" fill="#ff5f56"/><circle cx="26" cy="14" r="3.5" fill="#ffbd2e"/><circle cx="38" cy="14" r="3.5" fill="#27c93f"/>',
         f'<text x="{W//2}" y="17" fill="{DIM}" font-size="9" text-anchor="middle">{HANDLE}: ~$ ./stats.sh</text>',
         f'<line x1="0" y1="28" x2="{W}" y2="28" stroke="#21262d"/>']

    cw, ch, gx, gy, x0, y0 = 191, 88, 10, 10, 14, 40
    cards = [
        ("current streak", str(cur[0]), "days", rng(cur), GREEN, None),
        ("longest streak", str(lng[0]), "days", rng(lng), GREEN, None),
        ("contributions", f"{total:,}", "", "in the last year", WHITE, None),
        ("active days", str(active), f"/ {len(past)}", f"{active_pct}% of the last year", WHITE, None),
        ("best day", str(best["count"]), "", fmt(date.fromisoformat(best["date"])), WHITE, None),
        ("avg / active day", f"{avg:.1f}", "", "contributions", WHITE, None),
    ]
    for i, (lab, big, unit, sub, colr, _) in enumerate(cards):
        r, c = divmod(i, 2)
        x, y = x0 + c * (cw + gx), y0 + r * (ch + gy)
        u = f'<tspan class="unit" dx="6">{unit}</tspan>' if unit else ""
        o.append(f'<g class="c" style="animation-delay:{250 + i * 140}ms">'
                 f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="6" fill="#0d1117" stroke="#30363d"/>'
                 f'<text x="{x+12}" y="{y+22}" class="lab">$ {lab}</text>'
                 f'<text x="{x+12}" y="{y+56}" class="big" fill="{colr}">{big}{u}</text>'
                 f'<text x="{x+12}" y="{y+76}" class="sub">{sub}</text></g>')

    cy = y0 + 3 * (ch + gy)
    chh = H - cy - 14
    cwid = W - 2 * x0
    o.append(f'<rect x="{x0}" y="{cy}" width="{cwid}" height="{chh}" rx="6" fill="#0d1117" stroke="#30363d"/>')
    o.append(f'<text x="{x0+12}" y="{cy+22}" class="lab">$ contributions / month</text>')
    n = len(mvals)
    area_x, area_w = x0 + 16, cwid - 32
    slot = area_w / n
    bw = slot * 0.62
    base = cy + chh - 22
    maxh = chh - 70
    mx = max(v for _, v in mvals) or 1
    for i, (ym, v) in enumerate(mvals):
        h = max(3, v / mx * maxh) if v else 2
        bx = area_x + i * slot + (slot - bw) / 2
        delay = 900 + i * 60
        o.append(f'<rect class="b" style="animation-delay:{delay}ms" x="{bx:.1f}" y="{base - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="1.5" fill="{BAR}"/>')
        letter = date.fromisoformat(ym + "-01").strftime("%b")[0]
        o.append(f'<text x="{bx + bw/2:.1f}" y="{base + 14}" fill="{DIM}" font-size="9" text-anchor="middle">{letter}</text>')
        if v == mx:
            o.append(f'<text class="c" style="animation-delay:{delay + 500}ms" x="{bx + bw/2:.1f}" y="{base - h - 6:.1f}" fill="{WHITE}" font-size="9" font-weight="bold" text-anchor="middle">{v:,}</text>')
    o.append("</svg>")
    (ROOT / "stats.svg").write_text("\n".join(o))
    print("wrote stats.svg")


if __name__ == "__main__":
    main()
