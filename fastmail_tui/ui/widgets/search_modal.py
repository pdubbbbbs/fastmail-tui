"""Search modal with fuzzy matching."""

from typing import List, Optional, Callable
from textual.screen import ModalScreen
from textual.widgets import Input, Static, DataTable
from textual.containers import Vertical
from textual.binding import Binding
from rich.text import Text

from ...models.email import Email
from ...theme import COLORS, ICONS


class SearchModal(ModalScreen[Optional[Email]]):
  """Modal screen for searching emails with fuzzy matching.

  Returns the selected Email or None if cancelled.
  """

  BINDINGS = [
    Binding("escape", "cancel", "Cancel", show=True),
    Binding("enter", "select", "Select", show=True),
    Binding("down", "next_result", "Next", show=False),
    Binding("up", "prev_result", "Previous", show=False),
    Binding("ctrl+n", "next_result", "Next", show=False),
    Binding("ctrl+p", "prev_result", "Previous", show=False),
  ]

  DEFAULT_CSS = """
  SearchModal {
    align: center middle;
  }

  SearchModal > Vertical {
    width: 80%;
    max-width: 100;
    height: 70%;
    background: #12121A;
    border: solid #00D4FF;
    padding: 1;
  }

  SearchModal .title {
    color: #00D4FF;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
  }

  SearchModal Input {
    margin-bottom: 1;
  }

  SearchModal .results-count {
    color: #666688;
    margin-bottom: 1;
  }

  SearchModal DataTable {
    height: 1fr;
  }

  SearchModal DataTable > .datatable--cursor {
    background: #00D4FF33;
  }
  """

  def __init__(
    self,
    emails: List[Email],
    search_callback: Optional[Callable[[str], List[Email]]] = None,
    **kwargs,
  ):
    """Initialize search modal.

    Args:
      emails: Initial list of emails to search through
      search_callback: Optional async callback for server-side search
    """
    super().__init__(**kwargs)
    self._all_emails = emails
    self._filtered: List[Email] = emails[:50]  # Initial results
    self._search_callback = search_callback

  def compose(self):
    """Compose the modal."""
    with Vertical():
      yield Static(f" {ICONS['search']} Search Emails", classes="title")
      yield Input(placeholder="Type to search...", id="search-input")
      yield Static("", classes="results-count", id="results-count")
      yield DataTable(id="results-table", cursor_type="row")

  def on_mount(self) -> None:
    """Set up the results table."""
    table = self.query_one("#results-table", DataTable)
    table.add_columns("", "From", "Subject", "Date")
    table.cursor_type = "row"

    # Initial display
    self._update_results()
    self.query_one("#search-input", Input).focus()

  def on_input_changed(self, event: Input.Changed) -> None:
    """Handle search input changes."""
    query = event.value.strip().lower()

    if not query:
      self._filtered = self._all_emails[:50]
    else:
      # Simple fuzzy matching
      scored = []
      for email in self._all_emails:
        score = self._calculate_score(query, email)
        if score > 0:
          scored.append((score, email))

      # Sort by score (highest first)
      scored.sort(key=lambda x: x[0], reverse=True)
      self._filtered = [email for _, email in scored[:50]]

    self._update_results()

  def _calculate_score(self, query: str, email: Email) -> int:
    """Calculate match score for an email.

    Args:
      query: Search query (lowercase)
      email: Email to score

    Returns:
      Match score (0 = no match)
    """
    score = 0

    # Check subject
    subject_lower = email.subject.lower()
    if query in subject_lower:
      score += 100
      if subject_lower.startswith(query):
        score += 50

    # Check from
    from_lower = email.from_display.lower()
    if query in from_lower:
      score += 80
      if from_lower.startswith(query):
        score += 40

    # Check from email
    from_email_lower = email.from_email.lower()
    if query in from_email_lower:
      score += 60

    # Check preview
    preview_lower = email.preview.lower()
    if query in preview_lower:
      score += 30

    return score

  def _update_results(self) -> None:
    """Update the results display."""
    # Update count
    count = self.query_one("#results-count", Static)
    count.update(f" {len(self._filtered)} results")

    # Update table
    table = self.query_one("#results-table", DataTable)
    table.clear()

    for email in self._filtered:
      # Status
      status = Text()
      if email.is_unread:
        status.append(ICONS["unread"], style=COLORS["unread"])
      if email.is_starred:
        status.append(ICONS["starred"], style=COLORS["starred"])

      # From
      from_text = Text(email.from_display[:20], style=COLORS["foreground"])

      # Subject
      subject_text = Text(email.subject[:40] or "(no subject)", style=COLORS["foreground"])

      # Date
      date_text = Text(email.relative_date, style=COLORS["muted"])

      table.add_row(status, from_text, subject_text, date_text, key=email.id)

  def action_cancel(self) -> None:
    """Cancel search."""
    self.dismiss(None)

  def action_select(self) -> None:
    """Select current result."""
    table = self.query_one("#results-table", DataTable)
    if table.cursor_row is not None and 0 <= table.cursor_row < len(self._filtered):
      self.dismiss(self._filtered[table.cursor_row])
    else:
      self.dismiss(None)

  def action_next_result(self) -> None:
    """Move to next result."""
    table = self.query_one("#results-table", DataTable)
    table.action_cursor_down()

  def action_prev_result(self) -> None:
    """Move to previous result."""
    table = self.query_one("#results-table", DataTable)
    table.action_cursor_up()

  def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
    """Handle row double-click selection."""
    if event.row_key and event.row_key.value:
      email_id = str(event.row_key.value)
      for email in self._filtered:
        if email.id == email_id:
          self.dismiss(email)
          return
