"""Masked email management panel with password generation."""

from typing import Optional, List
from dataclasses import dataclass
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, DataTable, Button, Input, Switch, Label
from textual.message import Message
from textual.binding import Binding
from rich.text import Text
import pyperclip

from ...api.masked_email import MaskedEmail, MaskedEmailManager
from ...services.password_generator import (
  generate_password,
  generate_memorable_password,
  password_strength,
  PasswordOptions,
)
from ...theme import COLORS, ICONS


@dataclass
class NewLoginCredentials:
  """Credentials for a new website login."""
  masked_email: str
  password: str
  domain: str
  description: str


class MaskedEmailPanel(VerticalScroll):
  """Full-featured masked email management panel.

  Prominent feature for creating and managing masked emails
  with integrated password generation for new logins.
  """

  class CredentialsCreated(Message):
    """Message emitted when new login credentials are created."""

    def __init__(self, credentials: NewLoginCredentials) -> None:
      self.credentials = credentials
      super().__init__()

  BINDINGS = [
    Binding("n", "new_login", "New Login", show=True),
    Binding("space", "toggle_masked", "Toggle", show=True),
    Binding("c", "copy_email", "Copy Email", show=True),
    Binding("d", "delete_masked", "Delete", show=True),
    Binding("r", "refresh", "Refresh", show=True),
  ]

  DEFAULT_CSS = """
  MaskedEmailPanel {
    width: 100%;
    height: 100%;
    background: #0A0A0F;
    padding: 1;
  }

  MaskedEmailPanel > .panel-title {
    color: #00D4FF;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
    padding: 1;
    background: #12121A;
    border: solid #2A2A3A;
  }

  MaskedEmailPanel > .quick-create {
    background: #12121A;
    border: solid #00D4FF;
    padding: 1;
    margin-bottom: 1;
  }

  MaskedEmailPanel > .quick-create > .quick-title {
    color: #9945FF;
    text-style: bold;
    margin-bottom: 1;
  }

  MaskedEmailPanel > .quick-create Button {
    width: 100%;
    margin-top: 1;
  }

  MaskedEmailPanel > .list-section {
    margin-top: 1;
  }

  MaskedEmailPanel > .list-title {
    color: #E0E0E0;
    text-style: bold;
    margin-bottom: 1;
  }

  MaskedEmailPanel DataTable {
    height: auto;
    max-height: 20;
  }

  MaskedEmailPanel DataTable > .datatable--cursor {
    background: #00D4FF33;
  }

  MaskedEmailPanel > .stats {
    color: #666688;
    margin-top: 1;
  }

  MaskedEmailPanel > .help {
    color: #666688;
    margin-top: 1;
    text-align: center;
  }

  MaskedEmailPanel .active {
    color: #00FF88;
  }

  MaskedEmailPanel .disabled {
    color: #FF4444;
  }
  """

  def __init__(self, manager: Optional[MaskedEmailManager] = None, **kwargs):
    """Initialize masked email panel.

    Args:
      manager: MaskedEmailManager instance
    """
    super().__init__(**kwargs)
    self._manager = manager
    self._masked_emails: List[MaskedEmail] = []

  def compose(self):
    """Compose the panel."""
    yield Static(
      f" {ICONS['masked']} MASKED EMAIL MANAGER",
      classes="panel-title",
    )

    # Quick create section
    with Vertical(classes="quick-create"):
      yield Static(f"{ICONS['ai']} Quick New Login", classes="quick-title")
      yield Static(
        "Create a masked email + secure password for any website",
        classes="hint",
      )
      yield Input(
        placeholder="Website domain (e.g., example.com)",
        id="input-domain",
      )
      yield Input(
        placeholder="Description (e.g., Shopping account)",
        id="input-description",
      )
      yield Button(
        f"{ICONS['success']} Create Login Credentials",
        id="btn-create-login",
        variant="primary",
      )

    # Masked emails list
    yield Static("Your Masked Emails", classes="list-title")
    yield DataTable(id="masked-table", cursor_type="row")

    # Stats
    yield Static("", classes="stats", id="masked-stats")

    # Help
    yield Static(
      "n=New  Space=Toggle  c=Copy  d=Delete  r=Refresh",
      classes="help",
    )

  def on_mount(self) -> None:
    """Set up the table."""
    table = self.query_one("#masked-table", DataTable)
    table.add_columns("", "Email", "Domain", "Last Used")
    table.cursor_type = "row"

  def set_manager(self, manager: MaskedEmailManager) -> None:
    """Set the masked email manager.

    Args:
      manager: MaskedEmailManager instance
    """
    self._manager = manager

  async def refresh_masked_emails(self) -> None:
    """Fetch and display masked emails."""
    if not self._manager:
      return

    self._masked_emails = await self._manager.list_all()
    self._update_table()
    self._update_stats()

  def _update_table(self) -> None:
    """Update the masked emails table."""
    table = self.query_one("#masked-table", DataTable)
    table.clear()

    for me in self._masked_emails:
      # Status icon
      status = Text()
      if me.is_active:
        status.append(me.status_icon, style=f"bold {COLORS['success']}")
      else:
        status.append(me.status_icon, style=f"bold {COLORS['error']}")

      # Email address
      email_text = Text(me.email, style=COLORS["foreground"])

      # Domain/description
      domain_text = Text(
        me.domain_display if me.for_domain else me.description_display[:20],
        style=COLORS["muted"],
      )

      # Last used
      last_text = Text(me.last_used_display, style=COLORS["muted"])

      table.add_row(status, email_text, domain_text, last_text, key=me.id)

  def _update_stats(self) -> None:
    """Update the stats display."""
    stats = self.query_one("#masked-stats", Static)
    active = sum(1 for m in self._masked_emails if m.is_active)
    total = len(self._masked_emails)
    stats.update(f" {ICONS['success']} {active} active / {total} total masked emails")

  def get_selected_masked_email(self) -> Optional[MaskedEmail]:
    """Get the currently selected masked email."""
    table = self.query_one("#masked-table", DataTable)
    if table.cursor_row is not None and 0 <= table.cursor_row < len(self._masked_emails):
      return self._masked_emails[table.cursor_row]
    return None

  async def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button presses."""
    if event.button.id == "btn-create-login":
      await self._create_new_login()

  async def _create_new_login(self) -> None:
    """Create new masked email and password for a login."""
    if not self._manager:
      self.notify("Not connected to Fastmail", severity="error")
      return

    domain_input = self.query_one("#input-domain", Input)
    desc_input = self.query_one("#input-description", Input)

    domain = domain_input.value.strip()
    description = desc_input.value.strip() or f"Login for {domain}"

    if not domain:
      self.notify("Please enter a domain", severity="warning")
      domain_input.focus()
      return

    try:
      # Create masked email
      masked = await self._manager.create(
        for_domain=domain,
        description=description,
      )

      # Generate secure password
      password = generate_password(PasswordOptions(length=24))

      # Create credentials object
      credentials = NewLoginCredentials(
        masked_email=masked.email,
        password=password,
        domain=domain,
        description=description,
      )

      # Show credentials modal
      result = await self.app.push_screen_wait(
        CredentialsModal(credentials)
      )

      # Refresh list
      await self.refresh_masked_emails()

      # Clear inputs
      domain_input.value = ""
      desc_input.value = ""

      # Emit event
      self.post_message(self.CredentialsCreated(credentials))

      self.notify(f"Created {masked.email}", severity="information")

    except Exception as e:
      self.notify(f"Error: {str(e)[:50]}", severity="error")

  def action_new_login(self) -> None:
    """Focus the domain input for new login."""
    self.query_one("#input-domain", Input).focus()

  async def action_toggle_masked(self) -> None:
    """Toggle the selected masked email."""
    if not self._manager:
      return

    me = self.get_selected_masked_email()
    if me:
      try:
        new_state = await self._manager.toggle(me.id, me.state)
        await self.refresh_masked_emails()
        self.notify(f"{me.email} is now {new_state}")
      except Exception as e:
        self.notify(f"Error: {str(e)[:50]}", severity="error")

  def action_copy_email(self) -> None:
    """Copy selected email address to clipboard."""
    me = self.get_selected_masked_email()
    if me:
      try:
        pyperclip.copy(me.email)
        self.notify(f"Copied: {me.email}")
      except Exception:
        # pyperclip might fail in some environments
        self.notify(me.email, title="Copy this email")

  async def action_delete_masked(self) -> None:
    """Delete the selected masked email."""
    if not self._manager:
      return

    me = self.get_selected_masked_email()
    if me:
      # Confirm deletion
      confirmed = await self.app.push_screen_wait(
        ConfirmDeleteModal(me.email)
      )
      if confirmed:
        try:
          await self._manager.delete(me.id)
          await self.refresh_masked_emails()
          self.notify(f"Deleted: {me.email}")
        except Exception as e:
          self.notify(f"Error: {str(e)[:50]}", severity="error")

  async def action_refresh(self) -> None:
    """Refresh the masked email list."""
    await self.refresh_masked_emails()
    self.notify("Refreshed masked emails")


class CredentialsModal(ModalScreen[bool]):
  """Modal showing newly created login credentials."""

  BINDINGS = [
    Binding("escape", "close", "Close"),
    Binding("c", "copy_all", "Copy All"),
  ]

  DEFAULT_CSS = """
  CredentialsModal {
    align: center middle;
  }

  CredentialsModal > Vertical {
    width: 70;
    height: auto;
    background: #12121A;
    border: solid #00FF88;
    padding: 2;
  }

  CredentialsModal .title {
    color: #00FF88;
    text-style: bold;
    text-align: center;
    margin-bottom: 2;
  }

  CredentialsModal .section {
    color: #00D4FF;
    text-style: bold;
    margin-top: 1;
  }

  CredentialsModal .value {
    background: #1A1A24;
    padding: 1;
    margin-bottom: 1;
    border: solid #2A2A3A;
  }

  CredentialsModal .hint {
    color: #666688;
    text-align: center;
    margin-top: 1;
  }

  CredentialsModal .strength {
    margin-top: 1;
  }

  CredentialsModal .button-row {
    margin-top: 2;
    align: center middle;
    height: 3;
  }

  CredentialsModal Button {
    margin: 0 1;
  }
  """

  def __init__(self, credentials: NewLoginCredentials, **kwargs):
    """Initialize modal.

    Args:
      credentials: The newly created credentials
    """
    super().__init__(**kwargs)
    self._credentials = credentials

  def compose(self):
    """Compose the modal."""
    with Vertical():
      yield Static(
        f" {ICONS['success']} New Login Created!",
        classes="title",
      )

      yield Static(f"Website: {self._credentials.domain}", classes="section")

      yield Static(f"{ICONS['masked']} Email:", classes="section")
      yield Static(self._credentials.masked_email, classes="value", id="email-value")

      yield Static(f"{ICONS['encrypted']} Password:", classes="section")
      yield Static(self._credentials.password, classes="value", id="password-value")

      # Password strength
      strength = password_strength(self._credentials.password)
      strength_text = Text()
      strength_text.append("Strength: ", style=COLORS["muted"])
      strength_text.append(
        f"{strength['strength'].upper()} ",
        style=strength["color"],
      )
      strength_text.append(f"({strength['score']}/{strength['max_score']})", style=COLORS["muted"])
      yield Static(strength_text, classes="strength")

      yield Static(
        "Save these credentials in your password manager!",
        classes="hint",
      )

      with Horizontal(classes="button-row"):
        yield Button(
          f"{ICONS['success']} Copy Email",
          id="btn-copy-email",
          variant="default",
        )
        yield Button(
          f"{ICONS['encrypted']} Copy Password",
          id="btn-copy-password",
          variant="default",
        )
        yield Button(
          "Done",
          id="btn-close",
          variant="primary",
        )

  def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button presses."""
    if event.button.id == "btn-copy-email":
      try:
        pyperclip.copy(self._credentials.masked_email)
        self.notify("Email copied!")
      except Exception:
        pass
    elif event.button.id == "btn-copy-password":
      try:
        pyperclip.copy(self._credentials.password)
        self.notify("Password copied!")
      except Exception:
        pass
    elif event.button.id == "btn-close":
      self.dismiss(True)

  def action_close(self) -> None:
    """Close the modal."""
    self.dismiss(True)

  def action_copy_all(self) -> None:
    """Copy both email and password."""
    try:
      text = f"Email: {self._credentials.masked_email}\nPassword: {self._credentials.password}"
      pyperclip.copy(text)
      self.notify("Copied email and password!")
    except Exception:
      pass


class ConfirmDeleteModal(ModalScreen[bool]):
  """Confirmation modal for deleting a masked email."""

  BINDINGS = [
    Binding("escape", "cancel", "Cancel"),
    Binding("enter", "confirm", "Confirm"),
  ]

  DEFAULT_CSS = """
  ConfirmDeleteModal {
    align: center middle;
  }

  ConfirmDeleteModal > Vertical {
    width: 50;
    height: auto;
    background: #12121A;
    border: solid #FF4444;
    padding: 2;
  }

  ConfirmDeleteModal .title {
    color: #FF4444;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
  }

  ConfirmDeleteModal .message {
    text-align: center;
    margin-bottom: 1;
  }

  ConfirmDeleteModal .warning {
    color: #FFB800;
    text-align: center;
    margin-bottom: 2;
  }

  ConfirmDeleteModal .button-row {
    align: center middle;
    height: 3;
  }

  ConfirmDeleteModal Button {
    margin: 0 1;
  }
  """

  def __init__(self, email: str, **kwargs):
    """Initialize modal.

    Args:
      email: Email address being deleted
    """
    super().__init__(**kwargs)
    self._email = email

  def compose(self):
    """Compose the modal."""
    with Vertical():
      yield Static(f"{ICONS['warning']} Delete Masked Email?", classes="title")
      yield Static(self._email, classes="message")
      yield Static(
        "This cannot be undone. The address may be\nreassigned to someone else.",
        classes="warning",
      )

      with Horizontal(classes="button-row"):
        yield Button("Cancel", id="btn-cancel", variant="default")
        yield Button("Delete", id="btn-delete", variant="error")

  def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button presses."""
    if event.button.id == "btn-cancel":
      self.dismiss(False)
    elif event.button.id == "btn-delete":
      self.dismiss(True)

  def action_cancel(self) -> None:
    """Cancel deletion."""
    self.dismiss(False)

  def action_confirm(self) -> None:
    """Confirm deletion."""
    self.dismiss(True)
