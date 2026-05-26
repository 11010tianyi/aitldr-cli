"""
Local caching system for AI-generated TLDR pages.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

from .config import get_config_dir


@dataclass
class AiPageMetadata:
    """Metadata for AI-generated pages"""
    ai_generated: bool = True
    model: str = ""
    generated_at: str = ""
    confidence: str = "medium"
    sources: list = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if not self.generated_at:
            self.generated_at = datetime.now().strftime("%Y-%m-%d")


def get_ai_cache_dir() -> Path:
    """Get the AI cache directory"""
    return get_config_dir() / "ai"


def get_ratings_path() -> Path:
    """Get the ratings file path"""
    return get_config_dir() / "ratings.json"


def get_ai_page(command: str) -> Optional[str]:
    """Get AI-generated page from cache"""
    cache_dir = get_ai_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    page_path = cache_dir / f"{command}.md"

    if page_path.exists():
        with open(page_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def save_ai_page(command: str, content: str, metadata: AiPageMetadata) -> None:
    """Save AI-generated page to cache"""
    cache_dir = get_ai_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    page_path = cache_dir / f"{command}.md"

    # Add metadata as frontmatter
    metadata_lines = [
        "<!--",
        f"AI-Generated: {metadata.ai_generated}",
        f"Model: {metadata.model}",
        f"Generated-At: {metadata.generated_at}",
        f"Confidence: {metadata.confidence}",
    ]

    if metadata.sources:
        metadata_lines.append("Sources:")
        for source in metadata.sources:
            metadata_lines.append(f"- {source}")

    metadata_lines.append("-->")
    metadata_lines.append("")

    full_content = "\n".join(metadata_lines) + content

    with open(page_path, "w", encoding="utf-8") as f:
        f.write(full_content)


def delete_ai_page(command: str) -> bool:
    """Delete AI-generated page from cache"""
    cache_dir = get_ai_cache_dir()
    page_path = cache_dir / f"{command}.md"

    if page_path.exists():
        page_path.unlink()
        return True
    return False


def load_ratings() -> dict:
    """Load user ratings"""
    ratings_path = get_ratings_path()

    if not ratings_path.exists():
        return {}

    with open(ratings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_rating(command: str, rating: int) -> None:
    """Save a rating for a command"""
    ratings = load_ratings()
    ratings[command] = {"rating": rating}

    ratings_path = get_ratings_path()
    with open(ratings_path, "w", encoding="utf-8") as f:
        json.dump(ratings, f, indent=2)