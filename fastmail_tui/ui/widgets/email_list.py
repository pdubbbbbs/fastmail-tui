"""Email list widget with vim-style navigation."""

from typing import Optional, List, Set
from textual.widgets import DataTable
from textual.containers import Vertical
from textual.widgets import Static
from textual.message import Message
from textual.binding import Binding
from rich.text import Text

from ...models.email import Email
from ...theme import COLORS, ICONS


class EmailList(Vertical):
  """Email list with DataTable and vim-style navigation.

  Displays emails in a table with status indicators, sender,
  subject, and date. Supports multi-select for batch operations.
  """

  class EmailSelected(Message):
    """Message emitted when an email is selected."""

    def __init__(self, email: Email) -> None:
      self.email = email
      super().__init__()

  class EmailOpened(Message):
    """Message emitted when an email is opened (Enter pressed)."""

    def __init__(self, email: Email) -> None:
      self.email = email
      super().__init__()

  BINDINGS = [
    Binding("j", "cursor_down", "Down", show=False),
    Binding("k", "cursor_up", "Up", show=False),
    Binding("g", "go_top", "Top", show=False, key_display="gg"),
    Binding("G", "go_bottom", "Bottom", show=False),
    Binding("space", "toggle_select", "Select", show=False),
    Binding("ctrl+a", "select_all", "Select All", show=False),
  ]

  DEFAULT_CSS = """
  EmailList {
    height: 60%;
    background: #12121A;
    border-bottom: solid #2A2A3A;
  }

  EmailList > .title {
    background: #1A1A24;
    color: #00D4FF;
    text-style: bold;
    padding: 0 1;
    height: 1;
  }

  EmailList > DataTable {
    height: 1fr;
  }

  EmailList > DataTable > .datatable--cursor {
    background: #00D4FF33;
  }

  EmailList > DataTable > .datatable--header {
    background: #1A1A24;
    color: #00D4FF;
    text-style: bold;
  }

  EmailList > .status-line {
    background: #1A1A24;
    color: #666688;
    padding: 0 1;
    height: 1;
  }
  """

  def __init__(self, **kwargs):
    """Initialize email list."""
    super().__init__(**kwargs)
    self._emails: List[Email] = []
    self._selected_ids: Set[str] = set()
    self._current_mailbox_name: str = "Inbox"
    self._total_count: int = 0
    self._g_pressed: bool = False  # For gg binding

  def compose(self):
    """Compose the widget."""
    yield Static(
      f" {ICONS['inbox']} {self._current_mailbox_name}",
      classes="title",
      id="email-list-title",
    )
    yield DataTable(id="email-table", cursor_type="row", zebra_stripes=True)
    yield Static("", classes="status-line", id="email-list-status")

  def on_mount(self) -> None:
    """Set up the table on mount."""
    table = self.query_one("#email-table", DataTable)
    table.add_columns("", "From", "Subject", "Date", "")
    table.cursor_type = "row"

  def update_emails(
    self,
    emails: List[Email],
    mailbox_name: str = "Inbox",
    total_count: int = 0,
  ) -> None:
    """Update the email list display.

    Args:
      emails: List of Email objects to display
      mailbox_name: Name of current mailbox for title
      total_count: Total count for status line
    """
    self._emails = emails
    self._current_mailbox_name = mailbox_name
    self._total_count = total_count or len(emails)
    self._selected_ids.clear()

    # Update title
    title = self.query_one("#email-list-title", Static)
    mailbox_icon = ICONS.get(mailbox_name.lower(), ICONS["folder"])
    title.update(f" {mailbox_icon} {mailbox_name}")

    # Update table
    table = self.query_one("#email-table", DataTable)
    table.clear()

    for email in emails:
      self._add_email_row(table, email)

    # Update status
    self._update_status()

  def _add_email_row(self, table: DataTable, email: Email) -> None:
    """Add an email row to the table.

    Args:
      table: DataTable to add row to
      email: Email to display
    """
    # Status indicators
    status = Text()
    if email.id in self._selected_ids:
      status.append("", style=f"bold {COLORS['primary']}")
    elif email.is_unread:
      status.append(ICONS["unread"], style=f"bold {COLORS['unread']}")
    else:
      status.append(" ", style=COLORS["muted"])

    if email.is_starred:
      status.append(ICONS["starred"], style=COLORS["starred"])
    else:
      status.append(" ")

    if email.has_attachment:
      status.append(ICONS["attachment"], style=COLORS["secondary"])
    else:
      status.append(" ")

    # From field
    from_style = COLORS["foreground"]
    if email.is_unread:
      from_style = f"bold {COLORS['foreground']}"

    from_text = Text(email.from_display[:25], style=from_style)

    # Subject with preview
    subject_style = COLORS["foreground"]
    if email.is_unread:
      subject_style = f"bold {COLORS['foreground']}"

    subject_text = Text()
    subject_text.append(email.subject[:40] or "(no subject)", style=subject_style)
    if email.preview and len(email.subject) < 35:
      preview = email.preview[:30]
      subject_text.append(f" - {preview}", style=COLORS["muted"])

    # Date
    date_text = Text(email.relative_date, style=COLORS["muted"])

    # AI indicator
    ai_text = Text()
    if email.ai_category:
      ai_text.append(ICONS["ai"], style=COLORS["ai"])

    table.add_row(status, from_text, subject_text, date_text, ai_text, key=email.id)

  def _update_status(self) -> None:
    """Update the status line."""
    status = self.query_one("#email-list-status", Static)
    selected_count = len(self._selected_ids)

    if selected_count > 0:
      status.update(f" {selected_count} selected of {len(self._emails)} emails")
    else:
      status.update(f" {len(self._emails)} of {self._total_count} emails")

  def refresh_email(self, email: Email) -> None:
    """Refresh a single email's display.

    Args:
      email: Updated email data
    """
    # Find and update in our list
    for i, e in enumerate(self._emails):
      if e.id == email.id:
        self._emails[i] = email
        break

    # Re-render the table (simplest approach)
    table = self.query_one("#email-table", DataTable)
    table.clear()
    for e in self._emails:
      self._add_email_row(table, e)

  def get_selected_email(self) -> Optional[Email]:
    """Get the currently highlighted email.

    Returns:
      Email under cursor or None
    """
    table = self.query_one("#email-table", DataTable)
    if table.cursor_row is not None and 0 <= table.cursor_row < len(self._emails):
      return self._emails[table.cursor_row]
    return None

  def get_selected_emails(self) -> List[Email]:
    """Get all selected emails (for batch operations).

    Returns:
      List of selected Email objects
    """
    if self._selected_ids:
      return [e for e in self._emails if e.id in self._selected_ids]

    # If none explicitly selected, return current email
    current = self.get_selected_email()
    return [current] if current else []

  def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
    """Handle row selection."""
    if event.row_key and event.row_key.value:
      email_id = str(event.row_key.value)
      for email in self._emails:
        if email.id == email_id:
          self.post_message(self.EmailSelected(email))
          break

  def on_key(self, event) -> None:
    """Handle key events for gg binding."""
    if event.key == "g":
      if self._g_pressed:
        # Second g pressed - go to top
        self.action_go_top()
        self._g_pressed = False
        event.prevent_default()
      else:
        # First g pressed - wait for second
        self._g_pressed = True
        event.prevent_default()
    else:
      self._g_pressed = False

  def action_cursor_down(self) -> None:
    """Move cursor down (vim j)."""
    table = self.query_one("#email-table", DataTable)
    table.action_cursor_down()

  def action_cursor_up(self) -> None:
    """Move cursor up (vim k)."""
    table = self.query_one("#email-table", DataTable)
    table.action_cursor_up()

  def action_go_top(self) -> None:
    """Go to first email (vim gg)."""
    table = self.query_one("#email-table", DataTable)
    if len(self._emails) > 0:
      table.cursor_coordinate = (0, 0)

  def action_go_bottom(self) -> None:
    """Go to last email (vim G)."""
    table = self.query_one("#email-table", DataTable)
    if len(self._emails) > 0:
      table.cursor_coordinate = (len(self._emails) - 1, 0)

  def action_toggle_select(self) -> None:
    """Toggle selection of current email."""
    email = self.get_selected_email()
    if email:
      if email.id in self._selected_ids:
        self._selected_ids.remove(email.id)
      else:
        self._selected_ids.add(email.id)

      # Refresh to show selection
      table = self.query_one("#email-table", DataTable)
      table.clear()
      for e in self._emails:
        self._add_email_row(table, e)

      self._update_status()

  def action_select_all(self) -> None:
    """Select all visible emails."""
    if len(self._selected_ids) == len(self._emails):
      # All selected - deselect all
      self._selected_ids.clear()
    else:
      # Select all
      self._selected_ids = {e.id for e in self._emails}

    # Refresh display
    table = self.query_one("#email-table", DataTable)
    table.clear()
    for e in self._emails:
      self._add_email_row(table, e)

    self._update_status()

  def clear_selection(self) -> None:
    """Clear all selections."""
    self._selected_ids.clear()
    self._update_status()
