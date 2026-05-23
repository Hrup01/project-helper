from pathlib import Path

from langchain_core.tools import tool

from app.repository import repo_path
from app.utils import is_safe_child


def build_tools(project_id: str):
    root = repo_path(project_id)

    @tool
    def read_file(path: str) -> str:
        """Read a text file from the repository. Input is a repository-relative path."""
        target = root / path
        if not is_safe_child(root, target) or not target.exists() or not target.is_file():
            return "File not found or path is not allowed."
        data = target.read_bytes()[:80_000]
        return data.decode("utf-8", errors="replace")

    @tool
    def search_code(query: str) -> str:
        """Search text in repository files and return matching file paths and lines."""
        matches: list[str] = []
        lowered = query.lower()
        for path in root.rglob("*"):
            if len(matches) >= 80:
                break
            if any(part in {".git", "node_modules", ".venv", "__pycache__", "dist", "build"} for part in path.relative_to(root).parts):
                continue
            if not path.is_file() or path.stat().st_size > 200_000:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                if lowered in line.lower():
                    rel = path.relative_to(root).as_posix()
                    matches.append(f"{rel}:{number}: {line.strip()[:240]}")
                    break
        return "\n".join(matches) or "No matches found."

    @tool
    def list_files(prefix: str = "") -> str:
        """List repository files under an optional prefix."""
        base = root / prefix
        if not is_safe_child(root, base) or not base.exists():
            return "Path not found or path is not allowed."
        files = []
        for path in base.rglob("*"):
            if len(files) >= 200:
                break
            if path.is_file() and ".git" not in path.relative_to(root).parts:
                files.append(path.relative_to(root).as_posix())
        return "\n".join(files)

    return [read_file, search_code, list_files]
