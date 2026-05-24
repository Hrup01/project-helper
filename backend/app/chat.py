import json
from app import llm
from app.analyzer import get_project
from app.database import get_db
from app.tools import build_tools


SYSTEM = """你是 project-helper 的源码问答 Agent。
你必须优先使用工具读取文件、搜索代码或列出文件，然后再回答。
回答使用中文，面向初学者，指出依据来自哪些文件。"""


def add_message(project_id: str, role: str, content: str) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_messages (project_id, role, content) VALUES (?, ?, ?)",
            (project_id, role, content),
        )


def get_history(project_id: str) -> list[dict[str, str]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE project_id = ? ORDER BY id DESC LIMIT 10",
            (project_id,),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


async def stream_answer(project_id: str, question: str):
    project = get_project(project_id)
    if not project:
        yield {"type": "error", "message": "Project not found."}
        return

    add_message(project_id, "user", question)
    history = get_history(project_id)

    if llm.has_model():
        tools = {tool.name: tool for tool in build_tools(project_id)}
        yield {"type": "tool", "message": "调用工具：list_files()"}
        file_list = tools["list_files"].invoke({"prefix": ""})
        yield {"type": "tool", "message": f"调用工具：search_code({question[:80]})"}
        search_result = tools["search_code"].invoke({"query": question[:120]})
        messages = [
            *history[-6:],
            {
                "role": "user",
                "content": (
                    f"用户问题：{question}\n\n"
                    f"项目文件列表摘要：\n{file_list[:6000]}\n\n"
                    f"代码搜索结果：\n{search_result[:6000]}\n\n"
                    "请基于这些工具结果回答；如果依据不足，明确建议用户要查看的文件路径。"
                ),
            },
        ]
        answer_parts: list[str] = []
        async for token in llm.stream_chat(SYSTEM, messages):
            answer_parts.append(token)
            yield {"type": "delta", "content": token}
        answer = "".join(answer_parts)
    else:
        report = project.get("report") or ""
        answer = (
            "当前没有配置 DEEPSEEK_API_KEY，所以使用缓存报告做本地回答。\n\n"
            f"你的问题：{question}\n\n"
            "建议先查看报告中的“核心模块入口”和“阅读建议”。相关报告摘要如下：\n\n"
            f"{report[:1800]}"
        )
        yield {"type": "delta", "content": answer}

    add_message(project_id, "assistant", answer)
    yield {"type": "done"}


def sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
