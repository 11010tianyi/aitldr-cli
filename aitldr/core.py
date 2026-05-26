"""
Core lookup logic: Official > AI Cache > AI Generation
"""

import re
import httpx
import subprocess
import shutil
from typing import Optional, Tuple
from dataclasses import dataclass

from .config import Config, load_config
from .pages import get_official_page
from .cache import get_ai_page, save_ai_page, delete_ai_page, AiPageMetadata
from .ai import generate_page, generate_command_from_natural_language


def command_exists(command: str) -> bool:
    """Check if a command exists on the system"""
    if not command or command.strip() == "":
        return False

    try:
        result = subprocess.run(
            ["sh", "-c", f"command -v {command} 2>/dev/null || which {command} 2>/dev/null || type {command} 2>/dev/null"],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


@dataclass
class PageSource:
    """Source of the TLDR page"""
    source: str  # "official", "ai_cache", "ai_generated", "command"


DESTRUCTIVE_COMMANDS = [
    "rm -rf", "dd", "mkfs", "mkfs.", ":(){ :|:& };:", "fork bomb"
]


def is_natural_language(query: str) -> bool:
    """Check if input is natural language or a command"""
    # Check for Chinese characters
    if re.search(r"[一-鿿]", query):
        return True

    # Check for long sentences (more than 3 words with spaces)
    words = query.split()
    if len(words) > 3:
        return True

    # Check for natural language patterns
    natural_patterns = [
        r"删除|删除",  # delete
        r"查看|显示|list|show",  # view/show
        r"怎么|如何|how to",  # how to
        r"创建|新建|create|new",  # create
        r"搜索|查找|search|find",  # search
    ]

    for pattern in natural_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True

    return False


def is_destructive_command(content: str) -> bool:
    """Check if a command is destructive"""
    for dangerous in DESTRUCTIVE_COMMANDS:
        if dangerous in content:
            return True
    return False


def lookup_page(command: str, config: Config, offline: bool = False) -> Tuple[Optional[str], PageSource]:
    """
    Look up a TLDR page with priority: Official > AI Cache > AI Generation

    offline: Skip network requests (official pages), but allow AI generation
    """
    # Step 1: Check official page (skip if offline)
    if not offline:
        official = get_official_page(command)
        if official:
            return official, PageSource("official")

    # Step 2: Check AI cache
    cached = get_ai_page(command)
    if cached:
        return cached, PageSource("ai_cache")

    # Step 3: AI Generation
    # Skip command check in offline mode (allows forced generation)
    if not offline and config.general.cache_enabled:
        # Check if command exists before generating
        if not command_exists(command):
            return None, PageSource("ai_generated")

    # Generate AI page (offline mode skips command check)
    if config.general.cache_enabled:
        print(f"Generating AI page for '{command}'...")

        generated = generate_page(command, config)
        if generated:
            # Save to cache
            save_ai_page(command, generated.content, generated.metadata)
            return generated.content, PageSource("ai_generated")
        else:
            print("AI generation failed.")

    return None, PageSource("ai_generated")


def lookup_command(query: str, config: Config, explain: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Look up a command from natural language query.

    Returns (command, explanation)
    """
    command = generate_command_from_natural_language(query, config)

    if command:
        if explain:
            # Use AI to generate explanation for the full command
            explanation = generate_command_explanation(command, config)
            if explanation:
                return command, explanation

        return command, None

    return None, None


def generate_command_explanation(command: str, config: Config) -> Optional[str]:
    """Generate explanation for a command using AI."""
    provider = config.model.provider.lower()
    language = config.general.language

    if language == "zh":
        system_prompt = "你是一个命令行专家。简洁地解释给定的shell命令。说明每个命令的作用以及它们如何协同工作。用中文回答。"
        user_prompt = f"解释这个命令: {command}"
    else:
        system_prompt = "You are a command-line expert. Explain the given shell command concisely. Include what each command does and how they work together."
        user_prompt = f"Explain this command: {command}"

    if provider == "openai":
        if not config.openai.api_key:
            return None

        import openai
        client = openai.OpenAI(api_key=config.openai.api_key)

        try:
            response = client.chat.completions.create(
                model=config.model.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return None

    elif provider == "deepseek":
        if not config.deepseek.api_key:
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
                            "content": system_prompt,
                        },
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error generating explanation: {e}")
        finally:
            client.close()

    return None


def refresh_page(command: str, config: Config) -> bool:
    """Force refresh an AI-generated page"""
    # Check if command exists before generating
    if not command_exists(command):
        print(f"[yellow]Command '{command}' not found on this system.[/yellow]")
        return False

    # Delete cached page
    delete_ai_page(command)

    # Generate new page
    generated = generate_page(command, config)
    if generated:
        save_ai_page(command, generated.content, generated.metadata)
        return True

    return False