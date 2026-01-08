"""Status bar widget showing connection and sync status."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from textual.widgets import Static
from rich.text import Text

from ...theme import COLORS, ICONS


@dataclass
class ConnectionStatus:
  """Connection status data."""
  connected: bool = False
  account_email: str = ""
  error: Optional[str] = None


@dataclass
class SyncStatus:
  """Sync status data."""
  is_syncing: bool = False
  last_sync: Optional[datetime] = None
  pending_changes: int = 0
  error: Optional[str] = None


class StatusBar(Static):
  """Status bar showing connection, sync, and AI status.

  Displays at the bottom of the app with real-time status updates.
  """

  DEFAULT_CSS = """
  StatusBar {
    height: 1;
    background: #1A1A24;
    color: #666688;
    padding: 0 1;
    dock: bottom;
  }
  """

  def __init__(self, **kwargs):
    """Initialize status bar."""
    super().__init__(**kwargs)
    self._connection: ConnectionStatus = ConnectionStatus()
    self._sync: SyncStatus = SyncStatus()
    self._ai_enabled: bool = False
    self._ai_processing: bool = False

  def on_mount(self) -> None:
    """Initial render."""
    self._render()

  def set_connection_status(
    self,
    connected: bool,
    account_email: str = "",
    error: Optional[str] = None,
  ) -> None:
    """Update connection status.

    Args:
      connected: Whether connected to server
      account_email: Current account email
      error: Error message if any
    """
    self._connection = ConnectionStatus(
      connected=connected,
      account_email=account_email,
      error=error,
    )
    self._render()

  def set_sync_status(
    self,
    is_syncing: bool = False,
    last_sync: Optional[datetime] = None,
    pending_changes: int = 0,
    error: Optional[str] = None,
  ) -> None:
    """Update sync status.

    Args:
      is_syncing: Whether currently syncing
      last_sync: Last sync timestamp
      pending_changes: Number of pending changes
      error: Error message if any
    """
    self._sync = SyncStatus(
      is_syncing=is_syncing,
      last_sync=last_sync,
      pending_changes=pending_changes,
      error=error,
    )
    self._render()

  def set_ai_status(self, enabled: bool, processing: bool = False) -> None:
    """Update AI status.

    Args:
      enabled: Whether AI is enabled
      processing: Whether AI is currently processing
    """
    self._ai_enabled = enabled
    self._ai_processing = processing
    self._render()

  def _render(self) -> None:
    """Render the status bar."""
    parts = []

    # Connection status
    if self._connection.error:
      conn_text = Text()
      conn_text.append(f"{ICONS['error']} ", style=COLORS["error"])
      conn_text.append(self._connection.error[:30], style=COLORS["error"])
      parts.append(conn_text)
    elif self._connection.connected:
      conn_text = Text()
      conn_text.append(f"{ICONS['connected']} ", style=COLORS["success"])
      conn_text.append(
        self._connection.account_email or "Connected",
        style=COLORS["success"],
      )
      parts.append(conn_text)
    else:
      conn_text = Text()
      conn_text.append(f"{ICONS['disconnected']} ", style=COLORS["error"])
      conn_text.append("Disconnected", style=COLORS["error"])
      parts.append(conn_text)

    # Sync status
    if self._sync.is_syncing:
      sync_text = Text()
      sync_text.append(f" {ICONS['sync']} ", style=COLORS["primary"])
      sync_text.append("Syncing...", style=COLORS["primary"])
      parts.append(sync_text)
    elif self._sync.error:
      sync_text = Text()
      sync_text.append(f" {ICONS['warning']} ", style=COLORS["warning"])
      sync_text.append(f"Sync error: {self._sync.error[:20]}", style=COLORS["warning"])
      parts.append(sync_text)
    elif self._sync.last_sync:
      sync_text = Text()
      time_ago = self._format_time_ago(self._sync.last_sync)
      sync_text.append(f" {ICONS['success']} ", style=COLORS["muted"])
      sync_text.append(f"Synced {time_ago}", style=COLORS["muted"])
      parts.append(sync_text)

    # AI status
    if self._ai_enabled:
      ai_text = Text()
      if self._ai_processing:
        ai_text.append(f" {ICONS['ai']} ", style=COLORS["ai"])
        ai_text.append("AI processing...", style=COLORS["ai"])
      else:
        ai_text.append(f" {ICONS['ai']} ", style=COLORS["muted"])
        ai_text.append("AI ready", style=COLORS["muted"])
      parts.append(ai_text)

    # Combine parts with separator
    combined = Text()
    for i, part in enumerate(parts):
      combined.append_text(part)
      if i < len(parts) - 1:
        combined.append(" │ ", style=COLORS["border"])

    self.update(combined)

  def _format_time_ago(self, dt: datetime) -> str:
    """Format a datetime as relative time.

    Args:
      dt: Datetime to format

    Returns:
      Human-readable relative time string
    """
    now = datetime.now()
    diff = now - dt

    if diff.total_seconds() < 60:
      return "just now"
    elif diff.total_seconds() < 3600:
      mins = int(diff.total_seconds() / 60)
      return f"{mins}m ago"
    elif diff.total_seconds() < 86400:
      hours = int(diff.total_seconds() / 3600)
      return f"{hours}h ago"
    else:
      return dt.strftime("%b %d")
