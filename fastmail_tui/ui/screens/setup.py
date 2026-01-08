"""Setup screen for first-run configuration."""

from typing import Optional
from textual.screen import Screen
from textual.widgets import Input, Button, Static
from textual.containers import Vertical, Center
from textual.binding import Binding
from rich.text import Text

from ...services.credentials import CredentialManager
from ...theme import COLORS, ICONS


class SetupScreen(Screen):
  """First-run setup screen for entering credentials.

  Prompts user for Fastmail API token and optional Claude API key.
  """

  BINDINGS = [
    Binding("escape", "cancel", "Cancel", show=False),
    Binding("enter", "submit", "Submit", show=False),
  ]

  DEFAULT_CSS = """
  SetupScreen {
    align: center middle;
    background: #0A0A0F;
  }

  SetupScreen > Center > Vertical {
    width: 60;
    height: auto;
    background: #12121A;
    border: solid #00D4FF;
    padding: 2;
  }

  SetupScreen .title {
    color: #00D4FF;
    text-style: bold;
    text-align: center;
    margin-bottom: 2;
  }

  SetupScreen .subtitle {
    color: #E0E0E0;
    text-align: center;
    margin-bottom: 2;
  }

  SetupScreen .section {
    color: #9945FF;
    text-style: bold;
    margin-top: 2;
    margin-bottom: 1;
  }

  SetupScreen .hint {
    color: #666688;
    margin-bottom: 1;
  }

  SetupScreen Input {
    margin-bottom: 1;
  }

  SetupScreen .button-row {
    margin-top: 2;
    align: center middle;
    height: 3;
  }

  SetupScreen Button {
    margin: 0 1;
  }

  SetupScreen .error {
    color: #FF4444;
    margin-top: 1;
  }

  SetupScreen .optional {
    color: #666688;
    text-style: italic;
  }
  """

  def __init__(self, **kwargs):
    """Initialize setup screen."""
    super().__init__(**kwargs)
    self._error: Optional[str] = None

  def compose(self):
    """Compose the setup screen."""
    with Center():
      with Vertical():
        yield Static(f" {ICONS['inbox']} Fastmail TUI Setup", classes="title")
        yield Static(
          "Enter your credentials to get started",
          classes="subtitle",
        )

        # Fastmail section
        yield Static(f"{ICONS['encrypted']} Fastmail API Token", classes="section")
        yield Static(
          "Get your token from Fastmail:\nSettings → Privacy & Security → Integrations → API Tokens",
          classes="hint",
        )
        yield Input(
          placeholder="fmu1-xxxxxxxx-xxxxxxxxxxxx",
          password=True,
          id="input-fastmail-token",
        )

        # Claude section
        yield Static(f"{ICONS['ai']} Claude API Key (Optional)", classes="section")
        yield Static(
          "Get your key from console.anthropic.com\nEnables AI summaries and smart replies",
          classes="hint",
        )
        yield Input(
          placeholder="sk-ant-api03-xxxxxxxx",
          password=True,
          id="input-claude-key",
        )

        # Error display
        yield Static("", id="error-message", classes="error")

        # Buttons
        with Vertical(classes="button-row"):
          yield Button(
            f"{ICONS['success']} Save & Connect",
            id="btn-save",
            variant="primary",
          )

  def on_mount(self) -> None:
    """Focus the first input on mount."""
    self.query_one("#input-fastmail-token", Input).focus()

  def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button presses."""
    if event.button.id == "btn-save":
      self._save_credentials()

  def action_submit(self) -> None:
    """Handle enter key."""
    self._save_credentials()

  def action_cancel(self) -> None:
    """Cancel setup."""
    self.app.exit()

  def _save_credentials(self) -> None:
    """Validate and save credentials."""
    fastmail_token = self.query_one("#input-fastmail-token", Input).value.strip()
    claude_key = self.query_one("#input-claude-key", Input).value.strip()

    # Validate Fastmail token
    if not fastmail_token:
      self._show_error("Fastmail API token is required")
      return

    if not fastmail_token.startswith("fmu"):
      self._show_error("Invalid token format. Should start with 'fmu'")
      return

    # Save credentials
    try:
      creds = CredentialManager()
      creds.set_fastmail_token(fastmail_token)

      if claude_key:
        creds.set_claude_api_key(claude_key)

      # Dismiss screen - main app will connect
      self.dismiss(True)

    except Exception as e:
      self._show_error(f"Failed to save credentials: {str(e)}")

  def _show_error(self, message: str) -> None:
    """Display an error message.

    Args:
      message: Error message to display
    """
    error_widget = self.query_one("#error-message", Static)
    error_widget.update(f"{ICONS['error']} {message}")
