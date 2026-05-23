import json
from datetime import datetime

from app import llm
from app.database import get_db
from app.repository import clone_or_update_repo, current_branch
from app.scanner import compact_context, scan_repository
from app.utils import normalize_repo_url, project_id_for_url, repo_name_from_url


REPORT_SYSTEM = """你是资深全栈工程师和源码讲解老师。你的任务是把开源项目讲到初学者也能懂。
输出必须是中文 Markdown，结构清晰，包含项目概述、技术栈、目录结构、核心模块、数据流、设计模式、阅读建议、运行/二次开发建议。
解释要通俗，但不要牺牲技术准确性。"""


def _local_report(repo_name: str, summary: dict) -> str:
    tech = ", ".join(summary["technologies"]) or "暂未从文件特征识别出明确技术栈"
    dirs = "\n".join(f"- `{name}/`: 约 {count} 个文件" for name, count in summary["top_dirs"][:12])
    exts = ", ".join(f"{ext}({count})" for ext, count in summary["extensions"][:10])
    core_files = "\n".join(f"- `{item['path']}`：{item['lines']} 行" for item in summary["files"][:20])
    package = summary.get("package_json") or {}
    scripts = package.get("scripts") or {}
    scripts_md = "\n".join(f"- `{name}`: `{cmd}`" for name, cmd in scripts.items()) or "- 未发现 package.json scripts"

    return f"""# {repo_name} 源码分析报告

## 1. 项目概述

这个仓库包含约 **{summary['file_count']}** 个可识别源码/配置文件。系统根据目录、扩展名和关键配置做了本地静态分析；配置 `DEEPSEEK_API_KEY` 后会生成更深入的 AI 报告。

## 2. 技术栈

{tech}

主要文件类型：{exts}

## 3. 目录结构

{dirs or "- 仓库目录较平，未识别出明显的顶层模块。"}

## 4. 核心模块入口

以下文件通常值得优先阅读：

{core_files or "- 未找到可读取的文本源码文件。"}

## 5. 数据流和执行流

可以按这个顺序理解项目：

1. 先看 README、配置文件和依赖清单，确定项目解决什么问题。
2. 再找入口文件，例如 `main`、`app`、`server`、`index`、`src` 下的根组件。
3. 顺着入口看路由、服务层、数据访问层或组件树。
4. 最后阅读测试和示例，它们通常展示真实用法。

## 6. 设计模式观察

本地分析无法完整推断业务设计，但可以先关注这些信号：

- 是否有 `services`、`controllers`、`routes`、`models`、`schemas` 等分层目录。
- 是否有 `components`、`hooks`、`stores` 等前端状态和视图拆分。
- 是否通过配置文件集中管理环境差异。

## 7. 可用脚本

{scripts_md}

## 8. 阅读建议

- 第一遍只画地图：目录、入口、依赖、启动命令。
- 第二遍抓主线：一个请求或一个页面从入口到输出经过哪些文件。
- 第三遍看细节：错误处理、缓存、权限、测试和边界条件。
"""


def upsert_project(repo_url: str, status: str, report: str | None = None, summary_json: str | None = None, error: str | None = None, branch: str | None = None) -> str:
    normalized = normalize_repo_url(repo_url)
    project_id = project_id_for_url(normalized)
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO projects (id, repo_url, repo_name, branch, status, report, summary_json, error, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                branch=excluded.branch,
                status=excluded.status,
                report=COALESCE(excluded.report, projects.report),
                summary_json=COALESCE(excluded.summary_json, projects.summary_json),
                error=excluded.error,
                updated_at=excluded.updated_at
            """,
            (
                project_id,
                normalized,
                repo_name_from_url(normalized),
                branch,
                status,
                report,
                summary_json,
                error,
                datetime.utcnow().isoformat(),
            ),
        )
    return project_id


def get_project(project_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return dict(row) if row else None


async def analyze_repository(repo_url: str, force: bool = False):
    normalized = normalize_repo_url(repo_url)
    project_id = project_id_for_url(normalized)
    existing = get_project(project_id)
    if existing and existing["status"] == "completed" and existing["report"] and not force:
        yield {"type": "cached", "message": "已命中缓存，直接返回历史分析报告。", "project_id": project_id}
        yield {"type": "done", "project_id": project_id, "report": existing["report"]}
        return

    upsert_project(normalized, "running")
    yield {"type": "progress", "step": "clone", "message": "正在克隆或更新 GitHub 仓库..."}
    try:
        path = clone_or_update_repo(normalized)
        branch = current_branch(path)
        yield {"type": "progress", "step": "scan", "message": "正在扫描目录、依赖和源码文件..."}
        summary = scan_repository(path)
        summary_json = json.dumps(summary, ensure_ascii=False)

        yield {"type": "progress", "step": "report", "message": "正在生成通俗源码分析报告..."}
        if llm.has_model():
            context = compact_context(summary)
            report = await llm.complete_markdown(
                REPORT_SYSTEM,
                f"仓库：{repo_name_from_url(normalized)}\n\n源码摘要：\n{context}",
            )
        else:
            report = _local_report(repo_name_from_url(normalized), summary)

        upsert_project(normalized, "completed", report=report, summary_json=summary_json, branch=branch)
        yield {"type": "done", "project_id": project_id, "report": report}
    except Exception as exc:
        upsert_project(normalized, "failed", error=str(exc))
        yield {"type": "error", "project_id": project_id, "message": str(exc)}
