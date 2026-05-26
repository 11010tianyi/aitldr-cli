"""
Core lookup logic: Official > AI Cache > AI Generation
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass

from .config import Config, load_config
from .pages import get_official_page
from .cache import get_ai_page, save_ai_page, delete_ai_page, AiPageMetadata
from .ai import generate_page, generate_command_from_natural_language


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

    Returns (content, source)
    """
    # Step 1: Check official page
    official = get_official_page(command)
    if official:
        return official, PageSource("official")

    # Step 2: Check AI cache
    cached = get_ai_page(command)
    if cached:
        return cached, PageSource("ai_cache")

    # Step 3: AI Generation (skip if offline)
    if not offline and config.general.cache_enabled:
        print(f"No official page found. Generating AI page for '{command}'...")

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
            # Look up explanation for the base command
            base_command = command.split()[0]
            content, _ = lookup_page(base_command, config)
            if content:
                # Extract relevant info from content
                explanation = f"\nExplanation for '{base_command}':\n{content}"
                return command, explanation

        return command, None

    return None, None


def refresh_page(command: str, config: Config) -> bool:
    """Force refresh an AI-generated page"""
    # Delete cached page
    delete_ai_page(command)

    # Generate new page
    generated = generate_page(command, config)
    if generated:
        save_ai_page(command, generated.content, generated.metadata)
        return True

    return False