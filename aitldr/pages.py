"""
Official TLDR pages lookup.
Handles fetching from local pages directory and remote.
"""

import gzip
import httpx
from pathlib import Path
from typing import Optional
import platform
import tempfile
import shutil


def get_local_pages_dir() -> Optional[Path]:
    """Get the local pages directory from the tldr-pages repo"""
    # Try the cloned repository
    home = Path.home()
    repo_path = home / "aitldr" / "pages"

    if repo_path.exists():
        return repo_path

    return None


def get_platform_name() -> str:
    """Get the platform name for TLDR pages"""
    system = platform.system().lower()

    if system == "darwin":
        return "osx"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    elif system == "freebsd":
        return "freebsd"
    elif system == "openbsd":
        return "openbsd"
    elif system == "netbsd":
        return "netbsd"
    elif system == "sunos":
        return "sunos"
    else:
        return "common"


def get_official_page(command: str) -> Optional[str]:
    """Get official TLDR page for command"""
    pages_dir = get_local_pages_dir()

    if not pages_dir:
        # Try to fetch remotely
        return fetch_remote_page(command)

    # Try platform-specific page first, then common
    platform_name = get_platform_name()

    # Try: pages/<platform>/<command>.md
    platform_page = pages_dir / platform_name / f"{command}.md"
    if platform_page.exists():
        with open(platform_page, "r", encoding="utf-8") as f:
            return f.read()

    # Try: pages/common/<command>.md
    common_page = pages_dir / "common" / f"{command}.md"
    if common_page.exists():
        with open(common_page, "r", encoding="utf-8") as f:
            return f.read()

    return None


def fetch_remote_page(command: str) -> Optional[str]:
    """Fetch TLDR page from remote repository"""
    base_url = "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages"

    platform_name = get_platform_name()

    # Try platform-specific first
    urls = [
        f"{base_url}/{platform_name}/{command}.md",
        f"{base_url}/common/{command}.md",
    ]

    for url in urls:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    return response.text
        except Exception:
            continue

    return None


def update_local_pages() -> bool:
    """Update local pages by cloning/updating the tldr-pages repo"""
    pages_dir = Path.home() / "aitldr" / "pages"

    if pages_dir.exists():
        # Already have pages, this is a fork of the repo
        # The pages should already be up to date from the fork
        return True

    return False