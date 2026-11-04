"""GitHub saver retained from HAI and hardened for Study 2 archives.

Save user session data directly to a private GitHub repository using the GitHub API.
Requires a GitHub personal access token with repo permissions.
"""

import base64
import time

import requests

# GitHub answers 403 or 429 when the hourly API quota is exhausted.
RATE_LIMITED = (403, 429)


def save_to_github(
    repo: str,
    path: str,
    content: str,
    commit_message: str,
    github_token: str,
) -> tuple[bool, str | None]:
    """
    Save content to a file in a GitHub repo (creates or updates the file).

    Args:
        repo: 'username/repo' (e.g., 'owner/hiring-study-data-private')
        path: path in the repo (e.g., 'sessions/2026-05-25/session_abc123.json')
        content: string content to save
        commit_message: commit message
        github_token: GitHub personal access token with repo scope

    Returns:
        (success, error_message) where error_message is None on success.
    """
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    last_error = "The save has not completed."
    for attempt in range(3):
        if attempt:
            time.sleep(0.25 * 2 ** (attempt - 1))
        # Every write attempt needs a successful, fresh version lookup.
        # A failed GET is never treated as evidence that the file is absent.
        try:
            existing = requests.get(api_url, headers=headers, timeout=10)
            if existing.status_code == 200:
                sha = existing.json().get("sha")
                if not isinstance(sha, str) or not sha:
                    last_error = "The saved-file version could not be read."
                    continue
            elif existing.status_code == 404:
                sha = None
            elif existing.status_code in RATE_LIMITED:
                # Retrying cannot succeed before the quota resets; it only burns more calls.
                return False, f"Version lookup returned {existing.status_code}."
            else:
                last_error = f"Version lookup returned {existing.status_code}."
                continue
        except (requests.RequestException, ValueError, TypeError, AttributeError):
            last_error = "The saved-file version could not be reached."
            continue
        data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        }
        if sha:
            data["sha"] = sha
        try:
            response = requests.put(api_url, json=data, headers=headers, timeout=30)
            if response.status_code in (200, 201):
                return True, None
            last_error = f"Save returned {response.status_code}."
            if response.status_code in RATE_LIMITED:
                return False, last_error
        except requests.RequestException:
            last_error = "The save could not be confirmed."
        # Includes conflicts and ambiguous timeouts: fetch the version again.
    return False, last_error


def test_github_connection(github_token: str, repo: str) -> tuple[bool, str]:
    """Test GitHub API connection and repo access."""
    try:
        api_url = f"https://api.github.com/repos/{repo}"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            metadata = response.json()
            if metadata.get("private") is not True:
                return False, "Study data storage must use a private repository."
            if metadata.get("permissions", {}).get("push") is False:
                return False, "Study data storage does not permit writes."
            return True, "Private study-data repository is accessible."
        elif response.status_code == 404:
            return False, f"❌ Repository '{repo}' not found or no access"
        elif response.status_code == 401:
            return False, "❌ Invalid GitHub token"
        else:
            return False, f"❌ GitHub API error: {response.status_code}"
    except requests.RequestException as e:
        return False, f"❌ Connection failed: {e!s}"
