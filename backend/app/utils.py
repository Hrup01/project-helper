import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse


GITHUB_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/?$")


def normalize_repo_url(url: str) -> str:
    clean = url.strip().removesuffix(".git").rstrip("/")
    if not GITHUB_RE.match(clean):
        raise ValueError("Only HTTPS GitHub repository URLs are supported.")
    return clean


def project_id_for_url(url: str) -> str:
    return hashlib.sha256(normalize_repo_url(url).encode("utf-8")).hexdigest()[:16]


def repo_name_from_url(url: str) -> str:
    parsed = urlparse(normalize_repo_url(url))
    owner, repo = parsed.path.strip("/").split("/")[:2]
    return f"{owner}/{repo}"


def is_safe_child(root: Path, child: Path) -> bool:
    root_resolved = root.resolve()
    child_resolved = child.resolve()
    return child_resolved == root_resolved or root_resolved in child_resolved.parents
