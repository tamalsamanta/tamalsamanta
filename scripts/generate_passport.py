#!/usr/bin/env python3
"""Render README.md as a single ASCII passport page.

Everything is plain text: box-drawing characters, the Braille popcat from
popcat.txt, and live data from the GitHub API. No images, no icons, no
third-party badges.

    python scripts/generate_passport.py
    python scripts/generate_passport.py --date 2026-11-01 --no-network

The workflow in .github/workflows/passport.yml runs this once a day and commits
the result. Edit this file, not README.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import urllib.request

USER = "tamalsamanta"
WIDTH = 80
INNER = WIDTH - 2
GUTTER = 2
LABEL_WIDTH = 13
BRAILLE_BLANK = "\u2800"

FALLBACK = {
    "name": "Tamal Samanta",
    "repos": 14,
    "followers": 8,
    "following": 9,
    "gists": 0,
    "hireable": True,
    "created": dt.date(2019, 8, 6),
    "bio": "Wish deployments were free :/",
}

# One line per day. Rendered uppercase under REMARKS.
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

STACK = [
    "PYTHON", "JAVASCRIPT", "TYPESCRIPT", "REACT", "NODE.JS",
    "DJANGO", "C++", "MYSQL", "GIT", "FIGMA",
]

PROJECTS = [
    "MULTIPLAYER-WORDLE",
    "SHARED-CART-EXTENSION",
    "ZOOM-CLONE",
    "COMPETITIVECODING",
]


def fetch_profile() -> dict:
    """Pull public profile numbers. Never fatal: a stale passport beats no passport."""
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
        return {
            "name": data.get("name") or FALLBACK["name"],
            "repos": int(data["public_repos"]),
            "followers": int(data["followers"]),
            "following": int(data["following"]),
            "gists": int(data["public_gists"]),
            "hireable": bool(data.get("hireable")),
            "created": dt.date.fromisoformat(data["created_at"][:10]),
            "bio": (data.get("bio") or FALLBACK["bio"]).strip(),
        }
    except Exception as exc:  # noqa: BLE001
        print(f"warning: could not reach GitHub API ({exc}); using fallback data")
        return dict(FALLBACK)


def passport_number(profile: dict) -> str:
    """A stable document number derived from the account creation date + repo count."""
    created = profile["created"].strftime("%y%m%d")
    return f"TAM{created}{profile['repos']:03d}"


def read_cat() -> list[str]:
    path = pathlib.Path(__file__).resolve().parent.parent / "popcat.txt"
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        raise SystemExit(f"popcat.txt at {path} is empty")
    return lines


def edge(left: str, fill: str, right: str) -> str:
    return left + fill * INNER + right


def row(text: str = "") -> str:
    if len(text) > INNER:
        raise ValueError(f"line spills the border ({len(text)} > {INNER}): {text!r}")
    return "║" + text.ljust(INNER) + "║"


def left_right(left: str, right: str) -> str:
    gap = INNER - len(left) - len(right)
    if gap < GUTTER:
        raise ValueError(f"left/right fields collide: {left!r} / {right!r}")
    return row(left + " " * gap + right)


def field(label: str, value: str) -> str:
    return row("  " + label.ljust(LABEL_WIDTH) + "  " + value)


def labeled_items(
    label: str,
    items: list[str],
    width: int = INNER - GUTTER * 2 - LABEL_WIDTH,
) -> list[str]:
    """Flow a list of items under a label, never leaving a dangling separator."""
    groups: list[list[str]] = []
    current: list[str] = []
    for item in items:
        candidate = " / ".join(current + [item])
        if current and len(candidate) > width:
            groups.append(current)
            current = [item]
        else:
            current.append(item)
    if current:
        groups.append(current)

    return [
        "  " + (label if index == 0 else "").ljust(LABEL_WIDTH) + " / ".join(group)
        for index, group in enumerate(groups)
    ]


def header_block(art: list[str], profile: dict, issued: str) -> list[str]:
    """The popcat plus the cover text, centred above the passport page.

    Every art line is padded with Braille blanks, not spaces, so all twelve
    lines have identical rendered width even though Braille glyphs are wider
    than the surrounding monospace text.
    """
    art_width = max(len(line) for line in art)
    art = [line.ljust(art_width, BRAILLE_BLANK) for line in art]
    text = [
        "GITHUB PASSPORT",
        "REPUBLIC OF THE INTERNET",
        f'"{profile["bio"].upper()}"',
        "",
        profile["name"].upper(),
        "DESIGNER / DEVELOPER",
        "PUNE, IN",
        f"HOLDER SINCE {issued}",
    ]

    text_width = max(len(line) for line in text)
    block_width = GUTTER + art_width + 4 + text_width
    indent = " " * max(0, (WIDTH - block_width) // 2)

    lines = []
    for index, art_line in enumerate(art):
        right = text[index] if index < len(text) else ""
        lines.append((indent + "  " + art_line + "    " + right).rstrip())
    return lines


def mrz_line(prefix: str) -> str:
    content = prefix.ljust(INNER - GUTTER * 2, "<")
    return row(" " * GUTTER + content)


def build(profile: dict, art: list[str], today: dt.date) -> list[str]:
    mood = MOODS[today.toordinal() % len(MOODS)]
    doc_no = passport_number(profile)
    issued = profile["created"].strftime("%d %b %Y").upper()
    updated = today.strftime("%d %b %Y").upper()
    name_parts = profile["name"].upper().split()

    lines = [""]
    lines += header_block(art, profile, issued)
    lines.append("")

    lines += [
        edge("╔", "═", "╗"),
        left_right("  TYPE P    CODE INT", f"PASSPORT NO. {doc_no}  "),
        edge("╠", "═", "╣"),
    ]

    columns = [
        ("SURNAME", name_parts[-1]),
        ("GIVEN NAMES", " ".join(name_parts[:-1]) or "N/A"),
        ("GITHUB", USER.upper()),
        ("NATIONALITY", "INTERNET"),
        ("RESIDENCE", "PUNE, IN"),
        ("DATE OF ISSUE", issued),
        ("AUTHORITY", "GITHUB.COM"),
        ("OCCUPATION", "DESIGNER / DEVELOPER"),
        ("WEBSITE", "THEIPADKID.COM"),
        ("X / TWITTER", "@WTFTAMAL"),
        ("LINKEDIN", "IN/TAMALSAMANTA"),
        ("CONTACT", "TAMALSAMANTA2601@GMAIL.COM"),
        ("DATE OF EXPIRY", "NEVER"),
        ("STATUS", "ACTIVE"),
        ("LAST UPDATED", updated),
    ]
    lines += [field(label, value) for label, value in columns]

    lines.append(edge("╠", "═", "╣"))
    stats = (
        f"REPOS {profile['repos']:03d}",
        f"FOLLOWERS {profile['followers']:03d}",
        f"FOLLOWING {profile['following']:03d}",
        f"GISTS {profile['gists']:03d}",
        f"HIREABLE {'YES' if profile['hireable'] else 'NO'}",
    )
    lines.append(row("  " + "   ".join(stats)))
    lines += [row(line) for line in labeled_items("STACK", STACK)]
    lines += [row(line) for line in labeled_items("PROJECTS", PROJECTS)]
    lines.append(row("  " + "REMARKS".ljust(LABEL_WIDTH) + mood.upper()))

    mrz_name = name_parts[-1] + "<<" + "<".join(name_parts[:-1])
    lines += [
        edge("╠", "═", "╣"),
        mrz_line("P<INT<" + re.sub(r"[^A-Z<]", "", mrz_name)),
        mrz_line(
            f"{doc_no}"
            f"<FOL{profile['followers']:03d}"
            f"<FOLG{profile['following']:03d}"
            f"<GISTS{profile['gists']:03d}"
            f"<HIRE{1 if profile['hireable'] else 0}"
        ),
        edge("╚", "═", "╝"),
    ]
    return lines


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
    today = args.date or dt.datetime.now(dt.timezone.utc).date()
    profile = dict(FALLBACK) if args.no_network else fetch_profile()
    art = read_cat()

    lines = build(profile, art, today)
    for line in lines:
        if len(line) > WIDTH:
            raise ValueError(f"line is wider than {WIDTH} columns: {line!r}")

    readme = (
        "<!-- generated by scripts/generate_passport.py — edit that, not this -->\n\n"
        "```text\n"
        + "\n".join(lines)
        + "\n```\n"
    )
    output.write_text(readme, encoding="utf-8")
    print(f"wrote {output} ({today}, {profile['repos']} repos, {profile['followers']} followers)")


if __name__ == "__main__":
    main()
