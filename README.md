# aitldr - AI-native TLDR CLI

A CLI tool that first shows official TLDR pages, then falls back to AI-generated pages for missing commands.

## Features

- **Priority Lookup**: Official TLDR pages > Local AI cache > AI generation
- **Natural Language Mode**: Generate commands from natural language descriptions
- **Multi-Model Support**: OpenAI, DeepSeek, Ollama backends
- **Local Caching**: AI-generated pages are cached locally for instant access
- **Explain Mode**: Get detailed explanations for commands
- **Safety Warnings**: Alerts for destructive commands
- **Platform Detection**: Automatically shows platform-specific pages

## Installation

```bash
pip install -e .
```

Or run directly:

```bash
python -m aitldr
```

## Quick Start

### Initialize Configuration

```bash
aitldr init
```

### Look up a command

```bash
aitldr tar
```

### Natural language mode

```bash
aitldr "删除7天前的日志"
```

### With explanation

```bash
aitldr --explain "删除7天前的日志"
```

## Configuration

Edit `~/.aitldr/config.toml`:

```toml
[general]
explain_default = false
cache_enabled = true

[model]
provider = "openai"
model = "gpt-4o-mini"

[openai]
api_key = "env:OPENAI_API_KEY"

[deepseek]
api_key = "env:DEEPSEEK_API_KEY"

[ollama]
endpoint = "http://localhost:11434"
model = "qwen2:7b"
```

## Commands

| Command | Description |
|---------|-------------|
| `aitldr <command>` | Show TLDR page for command |
| `aitldr "<query>"` | Generate command from natural language |
| `aitldr --explain <query>` | Show command with explanation |
| `aitldr --refresh <command>` | Refresh AI-generated page |
| `aitldr --offline <command>` | Disable AI generation |
| `aitldr --model <provider> <command>` | Use specific AI provider |
| `aitldr rate <command> up|down` | Rate an AI-generated page |
| `aitldr submit <command>` | Get submission guide |
| `aitldr status` | Show configuration status |

## Architecture

```
Query
  ↓
Is Natural Language?
  ├─ Yes → Generate Command → AI → Output
  └─ No → Lookup Page
           ↓
        Official Page?
          ├─ Yes → Display
          └─ No → AI Cache?
                   ├─ Yes → Display (cached)
                   └─ No → AI Generate → Cache → Display
```

## Design Philosophy

- **AI is fallback, not replacement**: Official pages are always preferred
- **Keep it simple**: Default output is concise, use --explain for details
- **Local first**: AI-generated pages are cached for speed and offline use
- **Community contribution**: AI pages can be manually reviewed and submitted upstream

## License

MIT

## Disclaimer

AI-generated pages may contain inaccuracies. Always verify commands before executing.