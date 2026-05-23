import subprocess
from pathlib import Path

from app.config import get_settings
from app.utils import is_safe_child, normalize_repo_url, project_id_for_url


def repo_path(project_id: str) -> Path:
    return Path(get_settings().repos_dir) / project_id


def clone_or_update_repo(repo_url: str) -> Path:
    normalized = normalize_repo_url(repo_url)
    project_id = project_id_for_url(normalized)
    target = repo_path(project_id)
    repos_root = Path(get_settings().repos_dir)
    repos_root.mkdir(parents=True, exist_ok=True)
    if not is_safe_child(repos_root, target):
        raise ValueError("Invalid repository path.")

    if (target / ".git").exists():
        subprocess.run(["git", "-C", str(target), "fetch", "--all", "--prune"], check=True, capture_output=True, text=True)
        return target

    subprocess.run(
        ["git", "clone", "--depth", "1", normalized, str(target)],
        check=True,
        capture_output=True,
        text=True,
    )
    return target


def current_branch(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None
