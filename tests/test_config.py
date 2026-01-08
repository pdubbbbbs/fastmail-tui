"""Tests for configuration."""

import pytest
from pathlib import Path
import tempfile

from fastmail_tui.config import (
  Config,
  FastmailConfig,
  ClaudeConfig,
  CacheConfig,
  UIConfig,
  load_config,
  save_config,
)


def test_default_config():
  """Test default configuration values."""
  config = Config()

  assert config.fastmail.host == "api.fastmail.com"
  assert config.claude.enabled is True
  assert config.claude.model == "claude-sonnet-4-5"
  assert config.cache.enabled is True
  assert config.cache.max_messages == 500
  assert config.ui.vim_mode is True
  assert config.ui.refresh_interval == 30


def test_config_save_load():
  """Test saving and loading config."""
  with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
    config_path = Path(f.name)

  try:
    # Create custom config
    config = Config()
    config.ui.refresh_interval = 60
    config.claude.enabled = False

    # Save it
    save_config(config, config_path)

    # Load it back
    loaded = load_config(config_path)

    assert loaded.ui.refresh_interval == 60
    assert loaded.claude.enabled is False

  finally:
    config_path.unlink(missing_ok=True)


def test_load_missing_config():
  """Test loading non-existent config returns defaults."""
  config = load_config(Path("/nonexistent/path/config.yaml"))
  assert config.fastmail.host == "api.fastmail.com"
