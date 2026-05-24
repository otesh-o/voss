from config import (
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)


def _anthropic_reply(system_prompt: str, messages: list[dict]) -> str:
    import anthropic

    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your key here":
        raise RuntimeError("Missing ANTHROPIC_API_KEY.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def _openai_reply(system_prompt: str, messages: list[dict]) -> str:
    from openai import OpenAI

    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY.")

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            *messages,
        ],
    )
    return response.output_text


def _openrouter_reply(system_prompt: str, messages: list[dict]) -> str:
    from openai import OpenAI

    if not OPENROUTER_API_KEY:
        raise RuntimeError("Missing OPENROUTER_API_KEY.")

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    response = client.responses.create(
        model=OPENROUTER_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            *messages,
        ],
    )
    return response.output_text


def generate_reply(system_prompt: str, messages: list[dict]) -> str:
    provider = AI_PROVIDER

    if provider == "anthropic":
        return _anthropic_reply(system_prompt, messages)
    if provider == "openai":
        return _openai_reply(system_prompt, messages)
    if provider == "openrouter":
        return _openrouter_reply(system_prompt, messages)

    raise RuntimeError(
        f"Unsupported VOSS_PROVIDER '{provider}'. "
        "Use 'anthropic', 'openai', or 'openrouter'."
    )
