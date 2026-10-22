#!/usr/bin/env python3
"""Render README.md as a neofetch-style terminal card.

The popcat sits on the left, profile data is aligned to its right, and the
whole thing is plain text: Braille art, box characters, live GitHub numbers.
No images, no icons, no third-party badges.

    python scripts/generate_readme.py
    python scripts/generate_readme.py --date 2026-11-01 --no-network

The workflow in .github/workflows/readme.yml runs this once a day and commits
the result. Edit this file, not README.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import textwrap
import urllib.request
from zoneinfo import ZoneInfo

USER = "tamalsamanta"
TIMEZONE = ZoneInfo("Asia/Kolkata")

# Layout, measured in monospace character cells.
WINDOW = 92
LEFT_MARGIN = 2
ART_WIDTH = 24
GAP = 4
LABEL_WIDTH = 24
DATA_COL = LEFT_MARGIN + ART_WIDTH + GAP
DATA_WIDTH = WINDOW - DATA_COL
VALUE_WIDTH = DATA_WIDTH - LABEL_WIDTH

BRAILLE_BLANK = "\u2800"

FALLBACK = {
    "name": "Tamal Samanta",
    "repos": 14,
    "followers": 8,
    "following": 9,
    "gists": 0,
    "created": dt.date(2019, 8, 6),
    "bio": "Wish deployments were free :/",
    "stars": 0,
    "commits": 89,
    "hireable": True,
}

# One line per day, shown in the Status field.
MOODS = [
    "mrrp. shipping something small today.",
    "compiling... do not disturb.",
    "nine lives, still counting repos.",
    "the bug is a feature. probably.",
    "pet me after the deploy.",
    "one more commit. famous last words.",
    "five-minute FPS break. (never five.)",
    "pushing to main. living dangerously.",
    "friday deploy. what could go wrong.",
    "reinstalling node_modules. again.",
    "coffee, code, catnap, repeat.",
    "404: motivation not found. retrying.",
    "the linter and i aren't speaking.",
    "today's mood: 200 OK.",
]


def api_get(url: str, headers: dict[str, str]) -> object:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def fetch_profile() -> dict:
    """Pull public profile numbers. Never fatal: stale data beats no data."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER,
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    profile = dict(FALLBACK)
    try:
        data = api_get(f"https://api.github.com/users/{USER}", headers)
        profile.update(
            {
                "name": data.get("name") or FALLBACK["name"],
                "repos": int(data["public_repos"]),
                "followers": int(data["followers"]),
                "following": int(data["following"]),
                "gists": int(data["public_gists"]),
                "created": dt.date.fromisoformat(data["created_at"][:10]),
                "bio": (data.get("bio") or FALLBACK["bio"]).strip(),
                "hireable": bool(data.get("hireable")),
            }
        )
    except Exception as exc:  # noqa: BLE001
        print(f"warning: could not read profile ({exc}); using fallback data")

    try:
        repos = api_get(
            f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner",
            headers,
        )
        profile["stars"] = sum(int(repo.get("stargazers_count", 0)) for repo in repos)
    except Exception as exc:  # noqa: BLE001
        print(f"warning: could not count stars ({exc}); using fallback data")

    try:
        search = api_get(
            f"https://api.github.com/search/commits?q=author:{USER}&per_page=1",
            headers,
        )
        profile["commits"] = int(search.get("total_count", FALLBACK["commits"]))
    except Exception as exc:  # noqa: BLE001
        print(f"warning: could not count commits ({exc}); using fallback data")

    return profile


def read_cat() -> list[str]:
    path = pathlib.Path(__file__).resolve().parent.parent / "popcat.txt"
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        raise SystemExit(f"popcat.txt at {path} is empty")
    for line in lines:
        if len(line) > ART_WIDTH:
            raise SystemExit(
                f"popcat.txt line is {len(line)} cells wide; "
                f"the layout allows {ART_WIDTH}"
            )
    return lines


def field(label: str, value: str) -> list[str]:
    """One aligned label/value pair; long values wrap under the value column."""
    head = f"{label}:"
    if len(head) >= LABEL_WIDTH:
        raise ValueError(f"label too long ({len(head)}): {head!r}")

    wrapped = textwrap.wrap(
        str(value),
        width=VALUE_WIDTH,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]

    lines = [head.ljust(LABEL_WIDTH) + wrapped[0]]
    lines += [" " * LABEL_WIDTH + line for line in wrapped[1:]]
    return lines


def data_column(profile: dict, today: dt.date) -> list[str]:
    mood = MOODS[today.toordinal() % len(MOODS)]
    uptime = (today - profile["created"]).days
    joined = profile["created"].strftime("%d %b %Y")
    updated = today.strftime("%d %b %Y")

    rows = [
        "tamal@github",
        "─" * 14,
    ]
    rows += field("Name", profile["name"])
    rows += field("Role", "Designer / Developer")
    rows += field("Bio", f'"{profile["bio"]}"')
    rows += field("Host", "Pune, India")
    rows += field("Uptime", f"{uptime:,} days (since {joined})")
    rows += field("IDE", "VS Code")

    rows.append("")
    rows += field("Languages.Programming", "Python, JavaScript, TypeScript, C++")
    rows += field("Languages.Computer", "HTML, CSS, SQL")
    rows += field("Frameworks", "React, Node.js, Django")
    rows += field("Tools", "Git, Figma, MySQL")

    rows.append("")
    rows += field("Hobbies.Software", "Competitive programming, side projects")
    rows += field("Hobbies.Offline", "FPS games")

    rows.append("")
    rows.append("- Projects")
    rows += field("multiplayer-wordle", "Wordle but make that friend cry.")
    rows += field("shared-cart-extension", "Have friends who love shopping online?")
    rows += field("zoom-clone", "Zoom clone with Socket.IO + WebRTC.")
    rows += field("CompetitiveCoding", "Solutions from my end :)")

    rows.append("")
    rows.append("Contact")
    rows += field("Website", "theipadkid.com")
    rows += field("Email", "tamalsamanta2601@gmail.com")
    rows += field("LinkedIn", "in/tamalsamanta")
    rows += field("X", "@wtftamal")

    rows.append("")
    rows.append("- GitHub Stats")
    rows += field("Repos", f"{profile['repos']}")
    rows += field("Commits", f"{profile['commits']:,}")
    rows += field("Stars", f"{profile['stars']:,}")
    rows += field("Followers", f"{profile['followers']}")
    rows += field("Following", f"{profile['following']}")
    rows += field("Gists", f"{profile['gists']}")
    rows += field("Hireable", "yes" if profile["hireable"] else "no")

    rows.append("")
    rows += field("Last updated", updated)
    rows += field("Status", mood)
    return rows


def render(art: list[str], right_rows: list[str]) -> list[str]:
    """Join cat and data, keeping the data column pixel-aligned.

    Braille glyphs are wider than ordinary monospace, so every data row gets a
    gutter of exactly 24 Braille characters (the art, or blank Braille below
    it). This keeps the right-hand column still across fonts.
    """
    padded_art = [line.ljust(ART_WIDTH, BRAILLE_BLANK) for line in art]
    blank_gutter = BRAILLE_BLANK * ART_WIDTH

    lines: list[str] = []
    for index in range(max(len(padded_art), len(right_rows))):
        left = padded_art[index] if index < len(padded_art) else blank_gutter
        right = right_rows[index] if index < len(right_rows) else ""
        if index >= len(padded_art) and not right:
            lines.append("")
        else:
            lines.append((f"{' ' * LEFT_MARGIN}{left}{' ' * GAP}{right}").rstrip())
    return lines


def build(art: list[str], profile: dict, today: dt.date) -> list[str]:
    content = render(art, data_column(profile, today))
    rule = "  " + "─" * WINDOW
    return [
        "",
        "  ● README",
        rule,
        "",
        *content,
        "",
        rule,
        "  tamal@github:~$ █",
    ]


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

    output = (
        args.output
        or pathlib.Path(__file__).resolve().parent.parent / "README.md"
    )
    today = args.date or dt.datetime.now(TIMEZONE).date()
    profile = dict(FALLBACK) if args.no_network else fetch_profile()
    art = read_cat()

    lines = build(art, profile, today)
    for line in lines:
        if len(line) > WINDOW + 2:
            raise ValueError(f"line is wider than {WINDOW + 2} cells: {line!r}")

    readme = (
        "<!-- generated by scripts/generate_readme.py — edit that, not this -->\n\n"
        "```text\n"
        + "\n".join(lines)
        + "\n```\n"
    )
    output.write_text(readme, encoding="utf-8")
    print(
        f"wrote {output} ({today}, {profile['repos']} repos, "
        f"{profile['followers']} followers, {profile['commits']} commits)"
    )


if __name__ == "__main__":
    main()
