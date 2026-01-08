"""Main Textual application for Fastmail TUI."""

from typing import Optional
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer
from textual.screen import Screen

from .config import Config, load_config
from .theme import TEXTUAL_CSS, ICONS
from .services.credentials import CredentialManager
from .api.jmap_client import FastmailClient
from .api.masked_email import MaskedEmailManager
from .api.claude_client import ClaudeEmailAssistant
from .models.email import Email
from .models.mailbox import Mailbox

from .ui.widgets.mailbox_tree import MailboxTree
from .ui.widgets.email_list import EmailList
from .ui.widgets.email_preview import EmailPreview
from .ui.widgets.status_bar import StatusBar
from .ui.widgets.ai_panel import AIPanel
from .ui.widgets.search_modal import SearchModal
from .ui.widgets.compose_modal import ComposeModal, ComposedEmail
from .ui.widgets.masked_email_panel import MaskedEmailPanel
from .ui.screens.setup import SetupScreen


class InboxScreen(Screen):
  """Main inbox screen with email list and preview."""

  def compose(self) -> ComposeResult:
    """Compose the inbox layout."""
    with Horizontal(id="content"):
      yield MailboxTree(id="mailbox-tree")
      with Vertical(id="email-area"):
        yield EmailList(id="email-list")
        yield EmailPreview(id="email-preview")
      if self.app.config.ui.show_ai_panel:
        yield AIPanel(id="ai-panel")


class MaskedEmailScreen(Screen):
  """Screen for managing masked emails."""

  def compose(self) -> ComposeResult:
    """Compose the masked email screen."""
    yield MaskedEmailPanel(id="masked-panel")


class FastmailTUI(App):
  """Privacy-focused, AI-enhanced Fastmail TUI client.

  Features:
  - Full email management (read, compose, reply, archive, delete)
  - Masked email management with password generation
  - Claude AI integration for summaries and smart replies
  - Vim-style keyboard navigation
  - IlluminatiNebula theme
  """

  TITLE = "Fastmail TUI"
  SUB_TITLE = "Privacy-First Email"
  CSS = TEXTUAL_CSS

  BINDINGS = [
    # Vim-style navigation (handled in widgets)
    Binding("j", "cursor_down", "Down", show=False),
    Binding("k", "cursor_up", "Up", show=False),

    # Quick actions
    Binding("a", "archive", "Archive", show=True),
    Binding("d", "delete", "Delete", show=True),
    Binding("r", "reply", "Reply", show=True),
    Binding("R", "reply_all", "Reply All", show=False),
    Binding("f", "forward", "Forward", show=True),
    Binding("c", "compose", "Compose", show=True),
    Binding("s", "star", "Star", show=False),
    Binding("u", "mark_unread", "Unread", show=False),

    # View controls
    Binding("enter", "open_email", "Open", show=False),
    Binding("escape", "back", "Back", show=False),
    Binding("/", "search", "Search", show=True),

    # AI features
    Binding("ctrl+s", "ai_summarize", "AI Sum", show=True),
    Binding("ctrl+r", "ai_reply", "AI Reply", show=False),

    # Masked emails (prominent feature)
    Binding("m", "masked_emails", "Masked", show=True),
    Binding("ctrl+m", "quick_masked", "New Masked", show=True),

    # System
    Binding("ctrl+l", "refresh", "Refresh", show=False),
    Binding("q", "quit", "Quit", show=True),
    Binding("?", "help", "Help", show=False),
  ]

  SCREENS = {
    "inbox": InboxScreen,
    "masked": MaskedEmailScreen,
  }

  def __init__(self, config: Optional[Config] = None):
    """Initialize the application.

    Args:
      config: Configuration object (loads from file if not provided)
    """
    super().__init__()
    self.config = config or load_config()
    self._credentials = CredentialManager()
    self._jmap_client: Optional[FastmailClient] = None
    self._masked_manager: Optional[MaskedEmailManager] = None
    self._ai_assistant: Optional[ClaudeEmailAssistant] = None
    self._current_mailbox: Optional[Mailbox] = None
    self._emails: list[Email] = []
    self._current_screen = "inbox"

  def compose(self) -> ComposeResult:
    """Compose the main application layout."""
    yield Header()
    yield Container(id="main")
    yield StatusBar(id="status-bar")
    yield Footer()

  async def on_mount(self) -> None:
    """Initialize on mount."""
    # Check for credentials
    if not self._credentials.has_fastmail_credentials():
      # Show setup screen
      result = await self.push_screen_wait(SetupScreen())
      if not result:
        self.exit()
        return

    # Connect to Fastmail
    await self._connect()

    # Push inbox screen
    await self.push_screen("inbox")

  async def _connect(self) -> None:
    """Connect to Fastmail and initialize services."""
    status_bar = self.query_one("#status-bar", StatusBar)
    status_bar.set_connection_status(False, "", None)

    token = self._credentials.get_fastmail_token()
    if not token:
      status_bar.set_connection_status(False, "", "No credentials")
      return

    try:
      # Initialize JMAP client
      self._jmap_client = FastmailClient(
        host=self.config.fastmail.host,
        token=token,
      )

      session = await self._jmap_client.connect()
      status_bar.set_connection_status(True, session.primary_email)

      # Initialize masked email manager
      self._masked_manager = MaskedEmailManager(session.client)

      # Initialize AI assistant if enabled
      if self.config.claude.enabled:
        api_key = self._credentials.get_claude_api_key()
        if api_key:
          self._ai_assistant = ClaudeEmailAssistant(
            api_key=api_key,
            model=self.config.claude.model,
          )
          status_bar.set_ai_status(True)

      # Load initial data
      await self._load_mailboxes()
      await self._load_inbox()

      # Start refresh timer
      self.set_interval(
        self.config.ui.refresh_interval,
        self._background_refresh,
      )

    except Exception as e:
      status_bar.set_connection_status(False, "", str(e)[:50])
      self.notify(f"Connection failed: {e}", severity="error")

  async def _load_mailboxes(self) -> None:
    """Load mailboxes into the tree."""
    if not self._jmap_client:
      return

    try:
      mailboxes = await self._jmap_client.get_mailboxes()
      tree = self.query_one("#mailbox-tree", MailboxTree)
      tree.update_mailboxes(mailboxes)

      # Select inbox by default
      inbox = self._jmap_client.get_mailbox_by_role("inbox")
      if inbox:
        self._current_mailbox = inbox
        tree.select_mailbox(inbox.id)

    except Exception as e:
      self.notify(f"Failed to load mailboxes: {e}", severity="error")

  async def _load_inbox(self) -> None:
    """Load inbox emails."""
    if not self._jmap_client or not self._current_mailbox:
      return

    try:
      self._emails = await self._jmap_client.get_emails(
        mailbox_id=self._current_mailbox.id,
        limit=self.config.ui.page_size,
      )

      email_list = self.query_one("#email-list", EmailList)
      email_list.update_emails(
        self._emails,
        self._current_mailbox.display_name,
        self._current_mailbox.total_emails,
      )

    except Exception as e:
      self.notify(f"Failed to load emails: {e}", severity="error")

  async def _background_refresh(self) -> None:
    """Background refresh of email list."""
    if not self._jmap_client or not self._current_mailbox:
      return

    status_bar = self.query_one("#status-bar", StatusBar)
    status_bar.set_sync_status(is_syncing=True)

    try:
      # Refresh mailboxes for unread counts
      mailboxes = await self._jmap_client.get_mailboxes(force_refresh=True)
      tree = self.query_one("#mailbox-tree", MailboxTree)
      tree.update_mailboxes(mailboxes)

      # Refresh current mailbox emails
      self._emails = await self._jmap_client.get_emails(
        mailbox_id=self._current_mailbox.id,
        limit=self.config.ui.page_size,
      )

      email_list = self.query_one("#email-list", EmailList)
      email_list.update_emails(
        self._emails,
        self._current_mailbox.display_name,
        self._current_mailbox.total_emails,
      )

      status_bar.set_sync_status(
        is_syncing=False,
        last_sync=datetime.now(),
      )

    except Exception as e:
      status_bar.set_sync_status(
        is_syncing=False,
        error=str(e)[:30],
      )

  # Event handlers

  async def on_mailbox_tree_mailbox_selected(
    self,
    event: MailboxTree.MailboxSelected,
  ) -> None:
    """Handle mailbox selection."""
    self._current_mailbox = event.mailbox
    await self._load_inbox()

  async def on_email_list_email_selected(
    self,
    event: EmailList.EmailSelected,
  ) -> None:
    """Handle email selection - show preview."""
    if not self._jmap_client:
      return

    # Fetch full email content
    full_email = await self._jmap_client.get_email_by_id(event.email.id)
    if full_email:
      preview = self.query_one("#email-preview", EmailPreview)
      preview.show_email(full_email)

      # Mark as read
      if full_email.is_unread:
        await self._jmap_client.mark_read([full_email.id])

      # Update AI panel
      if self.config.ui.show_ai_panel:
        ai_panel = self.query_one("#ai-panel", AIPanel)
        ai_panel.set_email(full_email)

  async def on_ai_panel_summarize_requested(
    self,
    event: AIPanel.SummarizeRequested,
  ) -> None:
    """Handle AI summarization request."""
    if not self._ai_assistant:
      self.notify("AI not configured", severity="warning")
      return

    preview = self.query_one("#email-preview", EmailPreview)
    email = preview.get_current_email()
    if not email:
      return

    ai_panel = self.query_one("#ai-panel", AIPanel)
    ai_panel.show_loading("Analyzing email...")

    try:
      content = email.body_text or email.preview
      summary = await self._ai_assistant.summarize_email(
        subject=email.subject,
        content=content,
      )
      ai_panel.show_summary(summary)

      # Update email with AI data
      email.ai_summary = summary.one_liner
      email.ai_category = summary.category
      email.ai_sentiment = summary.sentiment
      email.ai_action_items = summary.action_items

    except Exception as e:
      self.notify(f"AI error: {e}", severity="error")
      ai_panel.clear()

  async def on_ai_panel_smart_reply_requested(
    self,
    event: AIPanel.SmartReplyRequested,
  ) -> None:
    """Handle smart reply request."""
    if not self._ai_assistant:
      self.notify("AI not configured", severity="warning")
      return

    preview = self.query_one("#email-preview", EmailPreview)
    email = preview.get_current_email()
    if not email:
      return

    ai_panel = self.query_one("#ai-panel", AIPanel)
    ai_panel.show_loading("Generating replies...")

    try:
      content = email.body_text or email.preview
      replies = await self._ai_assistant.suggest_replies(
        subject=email.subject,
        content=content,
        sender=email.from_display,
      )
      ai_panel.show_replies(replies)

    except Exception as e:
      self.notify(f"AI error: {e}", severity="error")

  async def on_ai_panel_reply_selected(
    self,
    event: AIPanel.ReplySelected,
  ) -> None:
    """Handle smart reply selection."""
    preview = self.query_one("#email-preview", EmailPreview)
    email = preview.get_current_email()
    if not email:
      return

    # Open compose with AI-generated content
    result = await self.push_screen_wait(
      ComposeModal(
        reply_to=email,
        draft_body=event.reply.content,
      )
    )

    if result:
      self.notify("Email sent!", severity="information")

  # Actions

  async def action_archive(self) -> None:
    """Archive selected emails."""
    if not self._jmap_client:
      return

    email_list = self.query_one("#email-list", EmailList)
    emails = email_list.get_selected_emails()

    if emails:
      await self._jmap_client.archive([e.id for e in emails])
      await self._load_inbox()
      self.notify(f"Archived {len(emails)} email(s)")

  async def action_delete(self) -> None:
    """Delete selected emails."""
    if not self._jmap_client:
      return

    email_list = self.query_one("#email-list", EmailList)
    emails = email_list.get_selected_emails()

    if emails:
      await self._jmap_client.move_to_trash([e.id for e in emails])
      await self._load_inbox()
      self.notify(f"Deleted {len(emails)} email(s)")

  async def action_reply(self) -> None:
    """Reply to current email."""
    preview = self.query_one("#email-preview", EmailPreview)
    email = preview.get_current_email()

    if email:
      result = await self.push_screen_wait(
        ComposeModal(reply_to=email)
      )
      if result:
        self.notify("Reply sent!")

  async def action_reply_all(self) -> None:
    """Reply all to current email."""
    preview = self.query_one("#email-preview", EmailPreview)
    email = preview.get_current_email()

    if email:
      result = await self.push_screen_wait(
        ComposeModal(reply_to=email, reply_all=True)
      )
      if result:
        self.notify("Reply sent!")

  async def action_forward(self) -> None:
    """Forward current email."""
    preview = self.query_one("#email-preview", EmailPreview)
    email = preview.get_current_email()

    if email:
      result = await self.push_screen_wait(
        ComposeModal(reply_to=email, forward=True)
      )
      if result:
        self.notify("Email forwarded!")

  async def action_compose(self) -> None:
    """Compose new email."""
    result = await self.push_screen_wait(ComposeModal())
    if result:
      self.notify("Email sent!")

  async def action_star(self) -> None:
    """Toggle star on current email."""
    if not self._jmap_client:
      return

    email_list = self.query_one("#email-list", EmailList)
    email = email_list.get_selected_email()

    if email:
      if email.is_starred:
        await self._jmap_client.unstar([email.id])
      else:
        await self._jmap_client.star([email.id])

      # Refresh
      email_list.refresh_email(email)

  async def action_mark_unread(self) -> None:
    """Mark current email as unread."""
    if not self._jmap_client:
      return

    email_list = self.query_one("#email-list", EmailList)
    email = email_list.get_selected_email()

    if email:
      await self._jmap_client.mark_unread([email.id])
      email_list.refresh_email(email)

  async def action_search(self) -> None:
    """Open search modal."""
    result = await self.push_screen_wait(
      SearchModal(emails=self._emails)
    )
    if result:
      # Show selected email
      preview = self.query_one("#email-preview", EmailPreview)
      full_email = await self._jmap_client.get_email_by_id(result.id)
      if full_email:
        preview.show_email(full_email)

  async def action_masked_emails(self) -> None:
    """Switch to masked emails screen."""
    if self._current_screen == "masked":
      await self.switch_screen("inbox")
      self._current_screen = "inbox"
    else:
      await self.switch_screen("masked")
      self._current_screen = "masked"

      # Initialize masked panel
      if self._masked_manager:
        panel = self.query_one("#masked-panel", MaskedEmailPanel)
        panel.set_manager(self._masked_manager)
        await panel.refresh_masked_emails()

  async def action_quick_masked(self) -> None:
    """Quick create masked email (opens masked screen)."""
    await self.switch_screen("masked")
    self._current_screen = "masked"

    if self._masked_manager:
      panel = self.query_one("#masked-panel", MaskedEmailPanel)
      panel.set_manager(self._masked_manager)
      await panel.refresh_masked_emails()
      panel.action_new_login()

  async def action_ai_summarize(self) -> None:
    """Trigger AI summarization."""
    if self.config.ui.show_ai_panel:
      ai_panel = self.query_one("#ai-panel", AIPanel)
      ai_panel.post_message(AIPanel.SummarizeRequested())

  async def action_ai_reply(self) -> None:
    """Trigger AI smart reply."""
    if self.config.ui.show_ai_panel:
      ai_panel = self.query_one("#ai-panel", AIPanel)
      ai_panel.post_message(AIPanel.SmartReplyRequested())

  async def action_refresh(self) -> None:
    """Manual refresh."""
    await self._background_refresh()
    self.notify("Refreshed")

  def action_back(self) -> None:
    """Go back / clear selection."""
    if self._current_screen == "masked":
      self.action_masked_emails()
    else:
      preview = self.query_one("#email-preview", EmailPreview)
      preview.clear()

  def action_help(self) -> None:
    """Show help."""
    help_text = """
Keyboard Shortcuts:
  j/k      - Navigate up/down
  Enter    - Open email
  /        - Search
  c        - Compose
  r        - Reply
  f        - Forward
  a        - Archive
  d        - Delete
  s        - Star
  m        - Masked emails
  Ctrl+M   - Quick new masked
  Ctrl+S   - AI summarize
  q        - Quit
"""
    self.notify(help_text, title="Help")
