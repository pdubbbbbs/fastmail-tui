"""Configuration management with dataclasses and YAML loading."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class FastmailConfig:
  """Fastmail JMAP connection settings."""
  host: str = "api.fastmail.com"
  account_id: str = ""  # Retrieved from session


@dataclass
class ClaudeConfig:
  """Claude AI integration settings."""
  enabled: bool = True
  model: str = "claude-sonnet-4-5"
  summarize_threads: bool = True
  suggest_replies: bool = True
  categorize_emails: bool = True
  max_summary_tokens: int = 500


@dataclass
class CacheConfig:
  """Local cache settings - minimal by design."""
  enabled: bool = True
  max_messages: int = 500  # Recent messages only
  encrypt: bool = True
  path: Path = field(default_factory=lambda: Path.home() / ".cache" / "fastmail-tui")


@dataclass
class UIConfig:
  """UI preferences."""
  vim_mode: bool = True
  preview_lines: int = 10
  show_ai_panel: bool = True
  notification_sound: bool = False
  refresh_interval: int = 30  # seconds
  page_size: int = 50  # emails per page


@dataclass
class Config:
  """Main configuration container."""
  fastmail: FastmailConfig = field(default_factory=FastmailConfig)
  claude: ClaudeConfig = field(default_factory=ClaudeConfig)
  cache: CacheConfig = field(default_factory=CacheConfig)
  ui: UIConfig = field(default_factory=UIConfig)


def get_config_path() -> Path:
  """Get the configuration file path."""
  config_dir = Path.home() / ".config" / "fastmail-tui"
  config_dir.mkdir(parents=True, exist_ok=True)
  return config_dir / "config.yaml"


def load_config(config_path: Optional[Path] = None) -> Config:
  """Load configuration from YAML file."""
  if config_path is None:
    config_path = get_config_path()

  if not config_path.exists():
    return Config()

  with open(config_path, "r") as f:
    data = yaml.safe_load(f) or {}

  config = Config()

  if "fastmail" in data:
    config.fastmail = FastmailConfig(**data["fastmail"])

  if "claude" in data:
    config.claude = ClaudeConfig(**data["claude"])

  if "cache" in data:
    cache_data = data["cache"]
    if "path" in cache_data:
      cache_data["path"] = Path(cache_data["path"])
    config.cache = CacheConfig(**cache_data)

  if "ui" in data:
    config.ui = UIConfig(**data["ui"])

  return config


def save_config(config: Config, config_path: Optional[Path] = None) -> None:
  """Save configuration to YAML file."""
  if config_path is None:
    config_path = get_config_path()

  data = {
    "fastmail": {
      "host": config.fastmail.host,
      "account_id": config.fastmail.account_id,
    },
    "claude": {
      "enabled": config.claude.enabled,
      "model": config.claude.model,
      "summarize_threads": config.claude.summarize_threads,
      "suggest_replies": config.claude.suggest_replies,
      "categorize_emails": config.claude.categorize_emails,
      "max_summary_tokens": config.claude.max_summary_tokens,
    },
    "cache": {
      "enabled": config.cache.enabled,
      "max_messages": config.cache.max_messages,
      "encrypt": config.cache.encrypt,
      "path": str(config.cache.path),
    },
    "ui": {
      "vim_mode": config.ui.vim_mode,
      "preview_lines": config.ui.preview_lines,
      "show_ai_panel": config.ui.show_ai_panel,
      "notification_sound": config.ui.notification_sound,
      "refresh_interval": config.ui.refresh_interval,
      "page_size": config.ui.page_size,
    },
  }

  config_path.parent.mkdir(parents=True, exist_ok=True)
  with open(config_path, "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
