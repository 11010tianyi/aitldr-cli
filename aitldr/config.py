"""
Configuration management for aitldr.

Reads and writes ~/.aitldr/config.toml
"""

import os
import tomli
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """Model configuration"""
    provider: str = "openai"
    model: str = "gpt-4o-mini"


@dataclass
class OpenAIConfig:
    """OpenAI configuration"""
    api_key: Optional[str] = None


@dataclass
class DeepSeekConfig:
    """DeepSeek configuration"""
    api_key: Optional[str] = None


@dataclass
class OllamaConfig:
    """Ollama configuration"""
    endpoint: str = "http://localhost:11434"
    model: str = "qwen2:7b"


@dataclass
class GeneralConfig:
    """General configuration"""
    explain_default: bool = False
    cache_enabled: bool = True
    language: str = "zh"


@dataclass
class Config:
    """Main configuration"""
    general: GeneralConfig = field(default_factory=GeneralConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    deepseek: DeepSeekConfig = field(default_factory=DeepSeekConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)


def get_config_dir() -> Path:
    """Get the aitldr configuration directory"""
    return Path.home() / ".aitldr"


def get_config_path() -> Path:
    """Get the configuration file path"""
    return get_config_dir() / "config.toml"


def load_config() -> Config:
    """Load configuration from file or return defaults"""
    config_path = get_config_path()

    if not config_path.exists():
        return Config()

    try:
        with open(config_path, "rb") as f:
            data = tomli.load(f)

        config = Config()

        if "general" in data:
            config.general = GeneralConfig(**data["general"])
        if "model" in data:
            config.model = ModelConfig(**data["model"])
        if "openai" in data:
            config.openai = OpenAIConfig(**data["openai"])
        if "deepseek" in data:
            config.deepseek = DeepSeekConfig(**data["deepseek"])
        if "ollama" in data:
            config.ollama = OllamaConfig(**data["ollama"])

        # Resolve env: prefixed API keys
        if config.openai.api_key and config.openai.api_key.startswith("env:"):
            env_var = config.openai.api_key[4:]
            config.openai.api_key = os.environ.get(env_var)

        if config.deepseek.api_key and config.deepseek.api_key.startswith("env:"):
            env_var = config.deepseek.api_key[4:]
            config.deepseek.api_key = os.environ.get(env_var)

        return config
    except Exception:
        return Config()


def save_config(config: Config) -> None:
    """Save configuration to file"""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = get_config_path()

    # Convert to dict for TOML serialization
    data = {
        "general": {
            "explain_default": config.general.explain_default,
            "cache_enabled": config.general.cache_enabled,
            "language": config.general.language,
        },
        "model": {
            "provider": config.model.provider,
            "model": config.model.model,
        },
        "openai": {
            "api_key": config.openai.api_key or "env:OPENAI_API_KEY",
        },
        "deepseek": {
            "api_key": config.deepseek.api_key or "env:DEEPSEEK_API_KEY",
        },
        "ollama": {
            "endpoint": config.ollama.endpoint,
            "model": config.ollama.model,
        },
    }

    import tomli_w

    with open(config_path, "wb") as f:
        tomli_w.dump(data, f)