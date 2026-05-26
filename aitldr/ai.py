"""
AI generation for missing TLDR pages.
Supports multiple backends: OpenAI, DeepSeek, Ollama.
"""

import httpx
import os
from typing import Optional
from dataclasses import dataclass

from .config import Config
from .cache import AiPageMetadata


@dataclass
class GeneratedPage:
    """AI-generated TLDR page"""
    content: str
    metadata: AiPageMetadata


def get_openai_page(command: str, api_key: str, model: str = "gpt-4o-mini") -> Optional[GeneratedPage]:
    """Generate TLDR page using OpenAI"""
    import openai

    client = openai.OpenAI(api_key=api_key)

    prompt = f"""Generate a TLDR page for command: {command}

Requirements:
- Follow official tldr-pages format
- Maximum 8 examples
- Use concise wording
- Prefer real-world usage
- Use placeholders like {{{{file}}}}
- DO NOT invent options or commands
- Prefer official docs/man pages over hallucination
- Start with a brief description and link to official docs if known

Format:
# {command}

> Brief description
> More information: <official_url>

- Example description:
`{command} {{{{arg1}}}} {{{{arg2}}}}`

Generate only the markdown, no other text.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )

        content = response.choices[0].message.content or ""

        metadata = AiPageMetadata(
            model=model,
            sources=["openai_generation"],
        )

        return GeneratedPage(content=content, metadata=metadata)
    except Exception as e:
        print(f"Error generating page with OpenAI: {e}")
        return None


def get_deepseek_page(command: str, api_key: str, model: str = "deepseek-chat") -> Optional[GeneratedPage]:
    """Generate TLDR page using DeepSeek"""
    client = httpx.Client(timeout=30.0)

    prompt = f"""Generate a TLDR page for command: {command}

Requirements:
- Follow official tldr-pages format
- Maximum 8 examples
- Use concise wording
- Prefer real-world usage
- Use placeholders like {{{{file}}}}
- DO NOT invent options or commands
- Prefer official docs/man pages over hallucination

Format:
# {command}

> Brief description

- Example description:
`{command} {{{{arg1}}}}`

Generate only the markdown, no other text.
"""

    try:
        response = client.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 800,
            },
        )

        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            metadata = AiPageMetadata(
                model=model,
                sources=["deepseek_generation"],
            )

            return GeneratedPage(content=content, metadata=metadata)
    except Exception as e:
        print(f"Error generating page with DeepSeek: {e}")
    finally:
        client.close()

    return None


def get_ollama_page(command: str, endpoint: str, model: str) -> Optional[GeneratedPage]:
    """Generate TLDR page using Ollama"""
    client = httpx.Client(timeout=30.0)

    prompt = f"""Generate a TLDR page for command: {command}

Requirements:
- Follow official tldr-pages format
- Maximum 8 examples
- Use concise wording
- Prefer real-world usage
- Use placeholders like {{{{file}}}}
- DO NOT invent options or commands

Format:
# {command}

> Brief description

- Example description:
`{command} {{{{arg1}}}}`

Generate only the markdown, no other text.
"""

    try:
        response = client.post(
            f"{endpoint}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 800,
                },
            },
        )

        if response.status_code == 200:
            data = response.json()
            content = data.get("response", "")

            metadata = AiPageMetadata(
                model=model,
                sources=["ollama_generation"],
            )

            return GeneratedPage(content=content, metadata=metadata)
    except Exception as e:
        print(f"Error generating page with Ollama: {e}")
    finally:
        client.close()

    return None


def generate_page(command: str, config: Config) -> Optional[GeneratedPage]:
    """Generate a TLDR page using configured AI backend"""
    provider = config.model.provider.lower()

    if provider == "openai":
        if not config.openai.api_key:
            print("Error: OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
            return None
        return get_openai_page(command, config.openai.api_key, config.model.model)

    elif provider == "deepseek":
        if not config.deepseek.api_key:
            print("Error: DeepSeek API key not configured. Set DEEPSEEK_API_KEY environment variable.")
            return None
        return get_deepseek_page(command, config.deepseek.api_key, config.model.model)

    elif provider == "ollama":
        return get_ollama_page(command, config.ollama.endpoint, config.ollama.model)

    else:
        print(f"Error: Unknown AI provider: {provider}")
        return None


def generate_command_from_natural_language(query: str, config: Config) -> Optional[str]:
    """Generate a command from natural language description"""
    provider = config.model.provider.lower()

    if provider == "openai":
        import openai

        if not config.openai.api_key:
            print("Error: OpenAI API key not configured.")
            return None

        client = openai.OpenAI(api_key=config.openai.api_key)

        try:
            response = client.chat.completions.create(
                model=config.model.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a command-line expert. Generate the exact shell command that answers the user's request. Output only the command, no explanation.",
                    },
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
                max_tokens=200,
            )

            command = response.choices[0].message.content or ""
            return command.strip()
        except Exception as e:
            print(f"Error generating command: {e}")
            return None

    elif provider == "deepseek":
        if not config.deepseek.api_key:
            print("Error: DeepSeek API key not configured.")
            return None

        client = httpx.Client(timeout=30.0)

        try:
            response = client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.deepseek.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.model.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a command-line expert. Generate the exact shell command that answers the user's request. Output only the command, no explanation.",
                        },
                        {"role": "user", "content": query},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200,
                },
            )

            if response.status_code == 200:
                data = response.json()
                command = data["choices"][0]["message"]["content"] or ""
                return command.strip()
        except Exception as e:
            print(f"Error generating command: {e}")
        finally:
            client.close()

        return None

    return None