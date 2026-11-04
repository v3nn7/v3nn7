
import json
import os
import urllib.request
from html import escape
from pathlib import Path

TOKEN = os.environ["GH_TOKEN"]
OWNERS = ["v3nn7", "OSyxSoftware", "rynlanguage"]

def github(path):
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "v3nn7-profile-stats",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

repos = {}

for owner in OWNERS:
    page = 1
    while True:
        data = github(
            f"/users/{owner}/repos?per_page=100&page={page}&type=public"
        )
        for repo in data:
            if not repo["fork"]:
                repos[repo["full_name"]] = repo

        if len(data) < 100:
            break
        page += 1

stars = sum(r["stargazers_count"] for r in repos.values())
followers = github("/users/v3nn7")["followers"]
repo_count = len(repos)

def stat(x, label, value, color):
    return f"""
    <g transform="translate({x},0)">
      <rect width="216" height="110" rx="14"
            fill="#161b22" stroke="#30363d"/>
      <text x="108" y="48" text-anchor="middle"
            fill="{color}" font-size="31"
            font-weight="bold">{value:,}</text>
      <text x="108" y="78" text-anchor="middle"
            fill="#8b949e" font-size="13">{escape(label)}</text>
    </g>
    """

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
    width="700" height="160" viewBox="0 0 700 160">
  <rect width="700" height="160" rx="18" fill="#0d1117"/>
  <g font-family="Arial, sans-serif" transform="translate(14,20)">
    {stat(0, "TOTAL STARS", stars, "#00c9ff")}
    {stat(228, "REPOSITORIES", repo_count, "#a78bfa")}
    {stat(456, "FOLLOWERS", followers, "#58a6ff")}
  </g>
</svg>"""

Path("assets").mkdir(exist_ok=True)
Path("assets/github-stats.svg").write_text(svg, encoding="utf-8")

print(f"Stars: {stars}, Repos: {repo_count}, Followers: {followers}")
