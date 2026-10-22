#!/usr/bin/env python3
"""Render the little terminal cat that lives at the top of the profile README.

The card is a static SVG (no scripts, no external assets) so it renders fine
through GitHub's image proxy. It changes every day: the greeting rotates, the
footer shows the current date / GitHub stats, and the cat blinks and swishes
its tail on a loop.

Run it with:

    python scripts/generate_cat.py

The GitHub workflow in .github/workflows/cat.yml runs this once a day and
commits the result.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import pathlib
import textwrap
import urllib.request

USER = "tamalsamanta"
FALLBACK_STATS = (14, 8, dt.date(2019, 8, 6))
MOOD_WIDTH = 38

# The cat, in all its states. Leading whitespace is significant.
CAT_OPEN = r"""
      /\_/\
     ( o.o )
      > ^ <
     /     \
    /  | |  \
   (   |_|   )_
    \_______/
"""

CAT_SHUT = CAT_OPEN.replace("o.o", "-.-")

# One line per day. Keep them short-ish; long ones wrap automatically.
MOODS = [
    "mrrp. shipping something small today.",
    "compiling... do not disturb.",
    "nine lives, 14 repos. still counting.",
    "the bug is a feature. probably.",
    "pet me after the deploy.",
    "one more commit. famous last words.",
    "five-minute FPS break. (never five.)",
    "pushing to main. living dangerously.",
    "friday deploy. what could go wrong.",
    "reinstalling node_modules. again.",
    "coffee, code, catnap, repeat.",
    "wish deployments were free :/",
    "the linter and i aren't speaking.",
    "today's mood: 200 OK.",
]


def fetch_stats() -> tuple[int, int, dt.date]:
    """Public repo count, followers, and signup date. Never fatal."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        f"https://api.github.com/users/{USER}", headers=headers
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.load(response)
        return (
            int(data["public_repos"]),
            int(data["followers"]),
            dt.date.fromisoformat(data["created_at"][:10]),
        )
    except Exception as exc:  # noqa: BLE001 - a stale card beats a failed build
        print(f"warning: could not reach GitHub API ({exc}); using fallback stats")
        return FALLBACK_STATS


def escaped_lines(art: str) -> list[str]:
    lines = art.strip("\n").splitlines()
    return [html.escape(line, quote=False) for line in lines]


def cat_block(lines: list[str], cls: str, start_y: int) -> str:
    body = "\n".join(
        f'      <tspan x="56" dy="{0 if index == 0 else 26}">{line}</tspan>'
        for index, line in enumerate(lines)
    )
    return (
        f'    <text class="{cls}" x="56" y="{start_y}" fill="#e6edf3" '
        f'font-size="22" xml:space="preserve">\n{body}\n    </text>'
    )


def tail_groups() -> str:
    # Two tail positions, swapped by CSS. Absolute coordinates line up with the
    # bottom row of the cat art above (baseline 256).
    return """    <g class="tail-a" fill="#e6edf3" font-size="22" xml:space="preserve">
      <text x="240" y="256">~~</text>
    </g>
    <g class="tail-b" fill="#e6edf3" font-size="22" xml:space="preserve">
      <text x="240" y="248">~</text>
      <text x="252" y="256">~</text>
    </g>"""


def mood_block(day: dt.date) -> str:
    mood = MOODS[day.toordinal() % len(MOODS)]
    wrapped = textwrap.wrap(mood, width=MOOD_WIDTH) or [""]
    rows = "".join(
        f'\n      <tspan x="30" dy="{0 if index == 0 else 19}">'
        f'{"&gt; " if index == 0 else "  "}{html.escape(line)}</tspan>'
        for index, line in enumerate(wrapped)
    )
    return f'    <text x="30" y="298" fill="#7ee787" font-size="14">{rows}\n    </text>'


def svg(day: dt.date, repos: int, followers: int, joined: dt.date) -> str:
    days = (day - joined).days + 1
    stats = f"{repos:,} repos · {followers:,} followers"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="380" height="400" viewBox="0 0 380 400" role="img" aria-labelledby="title desc">
  <title id="title">tamal@github: an ASCII cat in a terminal</title>
  <desc id="desc">A blinking ASCII cat. Today's note: {html.escape(MOODS[day.toordinal() % len(MOODS)])}</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0d1117"/>
      <stop offset="1" stop-color="#161b22"/>
    </linearGradient>
    <style>
      .eyes-open, .eyes-shut, .tail-a, .tail-b, .cursor, .heart {{
        animation-duration: 6.4s;
        animation-iteration-count: infinite;
        animation-timing-function: linear;
      }}
      .eyes-open {{ animation-name: eyes-open; }}
      .eyes-shut {{ animation-name: eyes-shut; }}
      .tail-a, .tail-b {{ animation-duration: 2.6s; }}
      .tail-a {{ animation-name: tail-a; }}
      .tail-b {{ animation-name: tail-b; }}
      .cursor {{
        animation-duration: 1.1s;
        animation-name: cursor;
        animation-timing-function: steps(1, end);
      }}
      .heart {{
        animation-duration: 4.5s;
        animation-name: heart;
        animation-timing-function: ease-in-out;
      }}
      @keyframes eyes-open {{
        0%, 91% {{ opacity: 1; }}
        92%, 96% {{ opacity: 0; }}
        97%, 100% {{ opacity: 1; }}
      }}
      @keyframes eyes-shut {{
        0%, 91% {{ opacity: 0; }}
        92%, 96% {{ opacity: 1; }}
        97%, 100% {{ opacity: 0; }}
      }}
      @keyframes tail-a {{
        0%, 45% {{ opacity: 1; }}
        46%, 100% {{ opacity: 0; }}
      }}
      @keyframes tail-b {{
        0%, 45% {{ opacity: 0; }}
        46%, 100% {{ opacity: 1; }}
      }}
      @keyframes cursor {{
        0%, 49% {{ opacity: 1; }}
        50%, 100% {{ opacity: 0; }}
      }}
      @keyframes heart {{
        0%, 100% {{ opacity: 0.85; transform: translateY(0); }}
        50% {{ opacity: 0.45; transform: translateY(-7px); }}
      }}
      @media (prefers-reduced-motion: reduce) {{
        .eyes-open, .eyes-shut, .tail-a, .tail-b, .cursor, .heart {{ animation: none; }}
        .eyes-shut, .tail-b {{ opacity: 0; }}
      }}
    </style>
  </defs>

  <rect x="0.5" y="0.5" width="379" height="399" rx="16" fill="url(#bg)" stroke="#30363d"/>
  <rect x="0.5" y="0.5" width="379" height="37" rx="16" fill="#161b22"/>
  <rect x="0.5" y="20" width="379" height="17.5" fill="#161b22"/>
  <line x1="0.5" y1="38" x2="379.5" y2="38" stroke="#30363d"/>

  <circle cx="22" cy="19" r="5" fill="#ff5f56"/>
  <circle cx="40" cy="19" r="5" fill="#ffbd2e"/>
  <circle cx="58" cy="19" r="5" fill="#27c93f"/>
  <text x="78" y="23" fill="#8b949e" font-size="11" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">tamal@github: ~/cat</text>
  <text x="356" y="23" fill="#6e7681" font-size="11" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">day {days:,}</text>

  <g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
{cat_block(escaped_lines(CAT_OPEN), "eyes-open", 100)}
{cat_block(escaped_lines(CAT_SHUT), "eyes-shut", 100)}
{tail_groups()}

    <text class="heart" x="318" y="128" fill="#f778ba" font-size="18">&#9829;</text>

{mood_block(day)}

    <rect x="20" y="340" width="340" height="44" rx="8" fill="#0d1117" stroke="#21262d"/>
    <text x="32" y="367" font-size="12">
      <tspan fill="#7ee787">tamal@github</tspan><tspan fill="#8b949e">:~$ </tspan><tspan class="cursor" fill="#e6edf3">█</tspan>
    </text>
    <text x="348" y="367" fill="#6e7681" font-size="10.5" text-anchor="end">{stats}</text>
  </g>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, default=None)
    parser.add_argument(
        "--date",
        type=dt.date.fromisoformat,
        default=None,
        help="Override the date (YYYY-MM-DD), useful for testing.",
    )
    parser.add_argument(
        "--no-network", action="store_true", help="Use fallback stats instead of the API."
    )
    args = parser.parse_args()

    output = args.output or pathlib.Path(__file__).resolve().parent.parent / "assets" / "cat.svg"
    day = args.date or dt.datetime.now(dt.timezone.utc).date()
    repos, followers, joined = FALLBACK_STATS if args.no_network else fetch_stats()

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg(day, repos, followers, joined), encoding="utf-8")
    print(f"wrote {output} ({day}, {repos} repos, {followers} followers)")


if __name__ == "__main__":
    main()
