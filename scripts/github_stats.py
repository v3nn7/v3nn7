import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

TOKEN = os.environ["GH_TOKEN"]
USER = "v3nn7"
OWNERS = [USER, "OSyxSoftware", "rynlanguage"]
OUTPUT = Path("assets/github-stats.svg")
TOP_LANGUAGES = 6

# Linguist colors, lightened where the original is unreadable on #0d1117.
LANGUAGE_COLORS = {
    "Rust": "#dea584",
    "C": "#a8b9cc",
    "C++": "#f34b7d",
    "C#": "#3fb950",
    "Python": "#3572a5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Java": "#b07219",
    "Lua": "#6b7fd7",
    "Luau": "#00a2ff",
    "GDScript": "#478cbf",
    "Shell": "#89e051",
    "Batchfile": "#c1f12e",
    "HTML": "#e34c26",
    "CSS": "#663399",
    "Assembly": "#9a7b4f",
    "CMake": "#da3434",
    "Makefile": "#427819",
}
FALLBACK_COLORS = ["#00c9ff", "#a78bfa", "#58a6ff", "#6865ff", "#7ee787", "#ffa657"]
OTHER_COLOR = "#484f58"

WIDTH = 700
PAD = 20
CARD_GAP = 12
CARD_HEIGHT = 96
BAR_Y = 158
LEGEND_Y = 192
LEGEND_ROW = 22
LEGEND_COLUMNS = 3

SANS = "'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif"
MONO = "SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"


def github(path, attempts=3):
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "v3nn7-profile-stats",
        },
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code < 500 or attempt == attempts - 1:
                raise
        except urllib.error.URLError:
            if attempt == attempts - 1:
                raise
        time.sleep(5 * 2**attempt)


def fetch_repos():
    repos = {}
    for owner in OWNERS:
        page = 1
        while True:
            data = github(
                f"/users/{owner}/repos?per_page=100&page={page}&type=owner"
            )
            for repo in data:
                if not repo["fork"]:
                    repos[repo["full_name"]] = repo

            if len(data) < 100:
                break
            page += 1
    return repos


def fetch_languages(repos):
    languages = Counter()
    for name in repos:
        languages.update(github(f"/repos/{name}/languages"))

    total = sum(languages.values())
    if not total:
        return []

    top = languages.most_common(TOP_LANGUAGES)
    other = total - sum(size for _, size in top)
    if other:
        top.append(("Other", other))
    return [(name, size / total) for name, size in top]


def language_colors(languages):
    fallback = iter(FALLBACK_COLORS)
    colors = {}
    for name, _ in languages:
        if name == "Other":
            colors[name] = OTHER_COLOR
        else:
            colors[name] = LANGUAGE_COLORS.get(name) or next(fallback, OTHER_COLOR)
    return colors


def stat_card(index, label, value, color):
    width = (WIDTH - 2 * PAD - 3 * CARD_GAP) / 4
    x = PAD + index * (width + CARD_GAP)
    return f"""
  <g class="fade" style="animation-delay:{index * 0.12:.2f}s"
     transform="translate({x:.1f},{PAD})">
    <rect width="{width:.1f}" height="{CARD_HEIGHT}" rx="12"
          fill="#161b22" stroke="#30363d"/>
    <rect x="16" y="0" width="32" height="3" rx="1.5" fill="{color}"/>
    <text x="{width / 2:.1f}" y="50" text-anchor="middle"
          class="value" fill="{color}">{value:,}</text>
    <text x="{width / 2:.1f}" y="76" text-anchor="middle"
          class="label">{escape(label)}</text>
  </g>"""


def language_section(languages):
    colors = language_colors(languages)
    bar_width = WIDTH - 2 * PAD
    column_width = bar_width / LEGEND_COLUMNS

    segments = []
    x = PAD
    for name, share in languages:
        segments.append(
            f'<rect x="{x:.2f}" y="{BAR_Y}" width="{share * bar_width:.2f}" '
            f'height="10" fill="{colors[name]}"/>'
        )
        x += share * bar_width

    legend = []
    for i, (name, share) in enumerate(languages):
        row, column = divmod(i, LEGEND_COLUMNS)
        lx = PAD + column * column_width
        ly = LEGEND_Y + row * LEGEND_ROW
        legend.append(f"""
    <g class="fade" style="animation-delay:{0.5 + i * 0.06:.2f}s">
      <circle cx="{lx + 5:.1f}" cy="{ly - 4}" r="5" fill="{colors[name]}"/>
      <text x="{lx + 18:.1f}" y="{ly}" class="name">{escape(name)}
        <tspan class="pct">{share * 100:.1f}%</tspan></text>
    </g>""")

    return f"""
  <text x="{PAD}" y="{BAR_Y - 12}" class="label fade"
        style="animation-delay:0.45s">TOP LANGUAGES</text>
  <clipPath id="bar">
    <rect x="{PAD}" y="{BAR_Y}" width="{bar_width}" height="10" rx="5"/>
  </clipPath>
  <g clip-path="url(#bar)" class="fade" style="animation-delay:0.45s">
    <rect x="{PAD}" y="{BAR_Y}" width="{bar_width}" height="10" fill="#21262d"/>
    {"".join(segments)}
  </g>{"".join(legend)}"""


def render(stars, forks, repo_count, followers, languages):
    cards = [
        ("TOTAL STARS", stars, "#00c9ff"),
        ("TOTAL FORKS", forks, "#6865ff"),
        ("REPOSITORIES", repo_count, "#a78bfa"),
        ("FOLLOWERS", followers, "#58a6ff"),
    ]

    if languages:
        rows = -(-len(languages) // LEGEND_COLUMNS)
        height = LEGEND_Y + (rows - 1) * LEGEND_ROW + PAD + 2
        body = language_section(languages)
    else:
        height = PAD * 2 + CARD_HEIGHT
        body = ""

    summary = (
        f"{stars:,} stars, {forks:,} forks, {repo_count:,} repositories, "
        f"{followers:,} followers"
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}"
    role="img" aria-labelledby="title">
  <title id="title">GitHub stats: {summary}</title>
  <style>
    .value {{ font: 700 30px {SANS}; }}
    .label {{ font: 600 11px {MONO}; letter-spacing: 1.5px; fill: #8b949e; }}
    .name {{ font: 400 12px {SANS}; fill: #c9d1d9; }}
    .pct {{ fill: #8b949e; }}
    .fade {{ animation: fade 0.6s ease-out backwards; }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .fade {{ animation: none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="18"
        fill="#0d1117" stroke="#21262d"/>
  {"".join(stat_card(i, *card) for i, card in enumerate(cards))}
  {body}
</svg>
"""


def main():
    repos = fetch_repos()
    stars = sum(r["stargazers_count"] for r in repos.values())
    forks = sum(r["forks_count"] for r in repos.values())
    followers = github(f"/users/{USER}")["followers"]
    languages = fetch_languages(repos)

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(
        render(stars, forks, len(repos), followers, languages), encoding="utf-8"
    )

    print(f"Stars: {stars}, Forks: {forks}, Repos: {len(repos)}, Followers: {followers}")
    for name, share in languages:
        print(f"  {name}: {share:.1%}")


if __name__ == "__main__":
    main()
