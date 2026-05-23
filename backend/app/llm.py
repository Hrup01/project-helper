from openai import AsyncOpenAI

from app.config import get_settings


def has_model() -> bool:
    return bool(get_settings().deepseek_api_key)


def client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)


async def complete_markdown(system: str, user: str) -> str:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured.")
    response = await client().chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


async def stream_chat(system: str, messages: list[dict[str, str]]):
    settings = get_settings()
    async with client().chat.completions.stream(
        model=settings.deepseek_model,
        messages=[{"role": "system", "content": system}, *messages],
        temperature=0.2,
    ) as stream:
        async for event in stream:
            if event.type == "content.delta":
                yield event.content
