"""CLI entry point for Fastmail TUI."""

import click
from pathlib import Path

from .config import load_config, save_config, get_config_path, Config
from .services.credentials import CredentialManager


@click.group(invoke_without_command=True)
@click.option(
  "--config",
  "-c",
  type=click.Path(exists=False, path_type=Path),
  help="Path to config file",
)
@click.pass_context
def main(ctx, config):
  """Fastmail TUI - Privacy-focused terminal email client.

  Run without arguments to launch the TUI application.
  Use subcommands for configuration and utilities.
  """
  ctx.ensure_object(dict)
  ctx.obj["config_path"] = config

  # If no subcommand, launch the TUI
  if ctx.invoked_subcommand is None:
    launch_app(config)


def launch_app(config_path: Path = None):
  """Launch the Textual application."""
  from .app import FastmailTUI

  config = load_config(config_path)
  app = FastmailTUI(config=config)
  app.run()


@main.command()
@click.option("--fastmail-token", prompt=True, hide_input=True, help="Fastmail API token")
@click.option(
  "--claude-key",
  prompt="Claude API key (optional, press Enter to skip)",
  default="",
  hide_input=True,
  help="Claude API key for AI features",
)
def setup(fastmail_token, claude_key):
  """Set up credentials for Fastmail TUI.

  Stores credentials securely in your system keyring.
  """
  if not fastmail_token:
    click.echo("Error: Fastmail token is required", err=True)
    return

  creds = CredentialManager()
  creds.set_fastmail_token(fastmail_token)
  click.echo("✓ Fastmail token saved")

  if claude_key:
    creds.set_claude_api_key(claude_key)
    click.echo("✓ Claude API key saved")

  click.echo("\nSetup complete! Run 'fastmail-tui' or 'fm' to start.")


@main.command()
def config_path():
  """Show the configuration file path."""
  path = get_config_path()
  click.echo(f"Config file: {path}")
  if path.exists():
    click.echo("  Status: exists")
  else:
    click.echo("  Status: not created yet (using defaults)")


@main.command()
def clear_credentials():
  """Remove all stored credentials.

  This will log you out and require re-setup.
  """
  if click.confirm("Are you sure you want to remove all credentials?"):
    creds = CredentialManager()
    creds.delete_all()
    click.echo("✓ All credentials removed")


@main.command()
@click.option("--enable-ai/--disable-ai", default=None, help="Enable/disable AI features")
@click.option("--ai-model", type=str, help="Claude model to use")
@click.option("--refresh-interval", type=int, help="Refresh interval in seconds")
@click.option("--page-size", type=int, help="Emails per page")
@click.option("--show-ai-panel/--hide-ai-panel", default=None, help="Show/hide AI panel")
def configure(enable_ai, ai_model, refresh_interval, page_size, show_ai_panel):
  """Update configuration options."""
  config = load_config()
  changed = False

  if enable_ai is not None:
    config.claude.enabled = enable_ai
    changed = True
    click.echo(f"AI: {'enabled' if enable_ai else 'disabled'}")

  if ai_model:
    config.claude.model = ai_model
    changed = True
    click.echo(f"AI model: {ai_model}")

  if refresh_interval is not None:
    config.ui.refresh_interval = refresh_interval
    changed = True
    click.echo(f"Refresh interval: {refresh_interval}s")

  if page_size is not None:
    config.ui.page_size = page_size
    changed = True
    click.echo(f"Page size: {page_size}")

  if show_ai_panel is not None:
    config.ui.show_ai_panel = show_ai_panel
    changed = True
    click.echo(f"AI panel: {'shown' if show_ai_panel else 'hidden'}")

  if changed:
    save_config(config)
    click.echo("\n✓ Configuration saved")
  else:
    click.echo("No changes specified. Use --help to see options.")


@main.command()
def version():
  """Show version information."""
  from . import __version__
  click.echo(f"Fastmail TUI v{__version__}")


@main.command()
@click.option("--length", "-l", default=24, help="Password length")
@click.option("--memorable", "-m", is_flag=True, help="Generate memorable password")
@click.option("--words", "-w", default=4, help="Number of words (for memorable)")
def generate_password(length, memorable, words):
  """Generate a secure password.

  Useful for creating passwords for new masked email logins.
  """
  from .services.password_generator import (
    generate_password as gen_pw,
    generate_memorable_password,
    password_strength,
    PasswordOptions,
  )

  if memorable:
    password = generate_memorable_password(num_words=words)
  else:
    password = gen_pw(PasswordOptions(length=length))

  strength = password_strength(password)

  click.echo(f"\nPassword: {password}")
  click.echo(f"Length: {len(password)}")
  click.echo(f"Strength: {strength['strength'].upper()} ({strength['score']}/{strength['max_score']})")

  # Copy to clipboard if possible
  try:
    import pyperclip
    pyperclip.copy(password)
    click.echo("\n✓ Copied to clipboard")
  except Exception:
    pass


if __name__ == "__main__":
  main()
