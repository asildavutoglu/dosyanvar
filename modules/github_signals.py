"""GitHub profil ve repo sinyallerini toplayan modül.

hiring-agent'taki github.py adımının basitleştirilmiş bir versiyonu:
profili ve en aktif repoları çekip LLM'e bağlam olarak veriyoruz.
"""

import os

import requests

GITHUB_API = "https://api.github.com"
TIMEOUT = 10


def _headers():
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_github_signals(username: str, max_repos: int = 8) -> dict:
    """Kullanıcının profilini ve en son güncellenen repolarını döndürür."""
    profile_resp = requests.get(f"{GITHUB_API}/users/{username}", headers=_headers(), timeout=TIMEOUT)
    if profile_resp.status_code == 404:
        raise ValueError(f"'{username}' adında bir GitHub kullanıcısı bulunamadı.")
    profile_resp.raise_for_status()
    profile = profile_resp.json()

    repos_resp = requests.get(
        f"{GITHUB_API}/users/{username}/repos",
        params={"sort": "pushed", "per_page": max_repos},
        headers=_headers(),
        timeout=TIMEOUT,
    )
    repos_resp.raise_for_status()
    repos = repos_resp.json()

    repo_summaries = [
        {
            "name": r.get("name"),
            "description": r.get("description"),
            "language": r.get("language"),
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "is_fork": r.get("fork", False),
            "pushed_at": r.get("pushed_at"),
        }
        for r in repos
        if isinstance(r, dict)
    ]

    return {
        "username": username,
        "name": profile.get("name"),
        "bio": profile.get("bio"),
        "public_repos": profile.get("public_repos"),
        "followers": profile.get("followers"),
        "account_created": profile.get("created_at"),
        "top_repos": repo_summaries,
    }
