import json
from collections import Counter, defaultdict
from pathlib import Path

from app.config import get_settings


SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode",
    "target",
    "coverage",
}

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".java",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".env",
    ".html",
    ".css",
    ".scss",
    ".sql",
}

TECH_BY_FILE = {
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "package.json": "Node.js",
    "vite.config.js": "Vite",
    "vite.config.ts": "Vite",
    "next.config.js": "Next.js",
    "dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "pom.xml": "Maven/Java",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
}

TECH_BY_EXT = {
    ".py": "Python",
    ".vue": "Vue",
    ".ts": "TypeScript",
    ".tsx": "React/TypeScript",
    ".js": "JavaScript",
    ".jsx": "React",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
}


def _read_text(path: Path, max_bytes: int) -> str:
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


def scan_repository(root: Path) -> dict:
    settings = get_settings()
    files: list[dict] = []
    ext_counter: Counter[str] = Counter()
    techs: set[str] = set()
    top_dirs: defaultdict[str, int] = defaultdict(int)

    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        lower_name = path.name.lower()
        size = path.stat().st_size

        if path.relative_to(root).parts:
            top_dirs[path.relative_to(root).parts[0]] += 1
        if suffix:
            ext_counter[suffix] += 1
            if suffix in TECH_BY_EXT:
                techs.add(TECH_BY_EXT[suffix])
        if lower_name in TECH_BY_FILE:
            techs.add(TECH_BY_FILE[lower_name])
        if suffix not in TEXT_EXTENSIONS and lower_name not in TECH_BY_FILE:
            continue
        if len(files) >= settings.max_analyzed_files:
            continue
        if size > settings.max_file_bytes:
            continue

        content = _read_text(path, settings.max_file_bytes)
        files.append(
            {
                "path": rel,
                "size": size,
                "lines": content.count("\n") + 1,
                "preview": content[:4000],
            }
        )

    package_json = None
    package_path = root / "package.json"
    if package_path.exists():
        try:
            package_json = json.loads(_read_text(package_path, settings.max_file_bytes))
        except json.JSONDecodeError:
            package_json = None

    return {
        "file_count": sum(ext_counter.values()),
        "extensions": ext_counter.most_common(20),
        "technologies": sorted(techs),
        "top_dirs": sorted(top_dirs.items(), key=lambda item: item[1], reverse=True)[:20],
        "files": files,
        "package_json": package_json,
    }


def compact_context(summary: dict) -> str:
    file_lines = []
    for item in summary["files"][:80]:
        preview = item["preview"].strip().replace("\r\n", "\n")
        file_lines.append(f"## {item['path']} ({item['lines']} lines)\n{preview[:1800]}")
    return "\n\n".join(
        [
            f"Technologies: {', '.join(summary['technologies']) or 'Unknown'}",
            f"Top directories: {summary['top_dirs']}",
            f"Extensions: {summary['extensions']}",
            "\n\n".join(file_lines),
        ]
    )
