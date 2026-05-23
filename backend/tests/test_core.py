import pytest

from app.scanner import scan_repository
from app.utils import normalize_repo_url, project_id_for_url, repo_name_from_url


def test_normalize_repo_url_accepts_github_https():
    url = normalize_repo_url("https://github.com/owner/repo.git")
    assert url == "https://github.com/owner/repo"
    assert repo_name_from_url(url) == "owner/repo"
    assert len(project_id_for_url(url)) == 16


def test_normalize_repo_url_rejects_non_github():
    with pytest.raises(ValueError):
        normalize_repo_url("https://example.com/owner/repo")


def test_scan_repository_detects_python(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    summary = scan_repository(tmp_path)
    assert "Python" in summary["technologies"]
    assert summary["files"][0]["path"] in {"requirements.txt", "app.py"}
