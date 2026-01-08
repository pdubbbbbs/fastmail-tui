"""Email preview widget with markdown rendering."""

from typing import Optional
from textual.containers import VerticalScroll
from textual.widgets import Static, Markdown
from textual.binding import Binding
from rich.text import Text
from markdownify import markdownify

from ...models.email import Email
from ...theme import COLORS, ICONS


class EmailPreview(VerticalScroll):
  """Email preview panel with header and body.

  Displays email metadata and content with support for
  both plain text and HTML (converted to markdown).
  """

  BINDINGS = [
    Binding("j", "scroll_down", "Scroll Down", show=False),
    Binding("k", "scroll_up", "Scroll Up", show=False),
    Binding("ctrl+d", "page_down", "Page Down", show=False),
    Binding("ctrl+u", "page_up", "Page Up", show=False),
  ]

  DEFAULT_CSS = """
  EmailPreview {
    height: 40%;
    background: #0A0A0F;
    padding: 1;
    border-top: solid #2A2A3A;
  }

  EmailPreview > .email-header {
    margin-bottom: 1;
  }

  EmailPreview > .email-subject {
    color: #00D4FF;
    text-style: bold;
    margin-bottom: 1;
  }

  EmailPreview > .email-meta {
    color: #666688;
    margin-bottom: 1;
  }

  EmailPreview > .email-body {
    color: #E0E0E0;
  }

  EmailPreview > .empty-state {
    color: #666688;
    text-align: center;
    margin-top: 3;
  }

  EmailPreview Markdown {
    background: transparent;
    padding: 0;
  }
  """

  def __init__(self, **kwargs):
    """Initialize preview."""
    super().__init__(**kwargs)
    self._current_email: Optional[Email] = None

  def compose(self):
    """Compose the widget."""
    yield Static(
      "Select an email to preview",
      classes="empty-state",
      id="preview-empty",
    )
    yield Static("", classes="email-subject", id="preview-subject")
    yield Static("", classes="email-meta", id="preview-meta")
    yield Markdown("", id="preview-body")

  def on_mount(self) -> None:
    """Hide content initially."""
    self.query_one("#preview-subject").display = False
    self.query_one("#preview-meta").display = False
    self.query_one("#preview-body").display = False

  def show_email(self, email: Email) -> None:
    """Display an email in the preview.

    Args:
      email: Email to display
    """
    self._current_email = email

    # Hide empty state
    self.query_one("#preview-empty").display = False

    # Show content elements
    subject_widget = self.query_one("#preview-subject", Static)
    meta_widget = self.query_one("#preview-meta", Static)
    body_widget = self.query_one("#preview-body", Markdown)

    subject_widget.display = True
    meta_widget.display = True
    body_widget.display = True

    # Update subject
    subject_text = Text()
    if email.is_unread:
      subject_text.append(f"{ICONS['unread']} ", style=COLORS["unread"])
    if email.is_starred:
      subject_text.append(f"{ICONS['starred']} ", style=COLORS["starred"])
    subject_text.append(email.subject or "(no subject)", style=f"bold {COLORS['primary']}")
    subject_widget.update(subject_text)

    # Update metadata
    meta_lines = []

    # From
    from_text = Text()
    from_text.append("From: ", style=COLORS["muted"])
    from_text.append(email.from_display, style=COLORS["foreground"])
    if email.from_email and email.from_email != email.from_display:
      from_text.append(f" <{email.from_email}>", style=COLORS["muted"])
    meta_lines.append(from_text)

    # To
    if email.to_addresses:
      to_text = Text()
      to_text.append("To: ", style=COLORS["muted"])
      to_list = ", ".join(a.display for a in email.to_addresses[:3])
      if len(email.to_addresses) > 3:
        to_list += f" +{len(email.to_addresses) - 3} more"
      to_text.append(to_list, style=COLORS["foreground"])
      meta_lines.append(to_text)

    # CC
    if email.cc_addresses:
      cc_text = Text()
      cc_text.append("CC: ", style=COLORS["muted"])
      cc_list = ", ".join(a.short_display for a in email.cc_addresses[:3])
      if len(email.cc_addresses) > 3:
        cc_list += f" +{len(email.cc_addresses) - 3} more"
      cc_text.append(cc_list, style=COLORS["foreground"])
      meta_lines.append(cc_text)

    # Date
    date_text = Text()
    date_text.append("Date: ", style=COLORS["muted"])
    date_text.append(email.date_display, style=COLORS["foreground"])
    meta_lines.append(date_text)

    # Attachments
    if email.has_attachment:
      attach_text = Text()
      attach_text.append(f"{ICONS['attachment']} ", style=COLORS["secondary"])
      attach_text.append("Has attachments", style=COLORS["muted"])
      meta_lines.append(attach_text)

    # AI summary if available
    if email.ai_summary:
      ai_text = Text()
      ai_text.append(f"{ICONS['ai']} AI: ", style=COLORS["ai"])
      ai_text.append(email.ai_summary, style=COLORS["foreground"])
      meta_lines.append(ai_text)

    # Combine meta lines
    combined_meta = Text()
    for i, line in enumerate(meta_lines):
      combined_meta.append_text(line)
      if i < len(meta_lines) - 1:
        combined_meta.append("\n")

    meta_widget.update(combined_meta)

    # Update body
    body_content = self._get_body_content(email)
    body_widget.update(body_content)

    # Scroll to top
    self.scroll_home()

  def _get_body_content(self, email: Email) -> str:
    """Get the body content, converting HTML to markdown if needed.

    Args:
      email: Email to get body from

    Returns:
      Markdown-formatted body text
    """
    # Prefer text body
    if email.body_text:
      return email.body_text

    # Convert HTML to markdown
    if email.body_html:
      try:
        return markdownify(
          email.body_html,
          heading_style="ATX",
          strip=["script", "style"],
        )
      except Exception:
        # Fallback: strip tags crudely
        import re
        return re.sub(r"<[^>]+>", "", email.body_html)

    # Fall back to preview
    if email.preview:
      return email.preview

    return "*No content available*"

  def clear(self) -> None:
    """Clear the preview."""
    self._current_email = None

    # Show empty state
    self.query_one("#preview-empty").display = True

    # Hide content
    self.query_one("#preview-subject").display = False
    self.query_one("#preview-meta").display = False
    self.query_one("#preview-body").display = False

  def get_current_email(self) -> Optional[Email]:
    """Get the currently displayed email.

    Returns:
      Current Email or None
    """
    return self._current_email

  def action_scroll_down(self) -> None:
    """Scroll down (vim j in preview)."""
    self.scroll_relative(y=3)

  def action_scroll_up(self) -> None:
    """Scroll up (vim k in preview)."""
    self.scroll_relative(y=-3)

  def action_page_down(self) -> None:
    """Page down (ctrl+d)."""
    self.scroll_page_down()

  def action_page_up(self) -> None:
    """Page up (ctrl+u)."""
    self.scroll_page_up()
