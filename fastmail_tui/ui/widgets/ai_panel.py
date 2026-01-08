"""AI panel widget showing summaries and suggestions."""

from typing import Optional, List
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, Button
from textual.message import Message
from rich.text import Text

from ...models.email import Email, EmailCategory, EmailSentiment
from ...api.claude_client import EmailSummary, ReplyDraft
from ...theme import COLORS, ICONS


class AIPanel(Vertical):
  """AI panel showing email analysis and suggestions.

  Displays AI-generated summaries, action items, and smart reply
  suggestions for the currently selected email.
  """

  class ReplySelected(Message):
    """Message emitted when a reply suggestion is selected."""

    def __init__(self, reply: ReplyDraft) -> None:
      self.reply = reply
      super().__init__()

  class SummarizeRequested(Message):
    """Message emitted when user requests summarization."""
    pass

  class SmartReplyRequested(Message):
    """Message emitted when user requests smart replies."""
    pass

  DEFAULT_CSS = """
  AIPanel {
    width: 30;
    min-width: 25;
    max-width: 40;
    background: #12121A;
    border-left: solid #2A2A3A;
    padding: 1;
  }

  AIPanel > .title {
    color: #9945FF;
    text-style: bold;
    margin-bottom: 1;
  }

  AIPanel > .section-title {
    color: #00D4FF;
    text-style: bold;
    margin-top: 1;
    margin-bottom: 0;
  }

  AIPanel > .summary {
    color: #E0E0E0;
    margin-bottom: 1;
  }

  AIPanel > .category {
    margin-bottom: 1;
  }

  AIPanel > .action-item {
    color: #00FF88;
    padding-left: 1;
  }

  AIPanel > .key-point {
    color: #E0E0E0;
    padding-left: 1;
  }

  AIPanel > .reply-option {
    background: #1A1A24;
    border: solid #2A2A3A;
    margin-top: 1;
    padding: 1;
  }

  AIPanel > .reply-option:hover {
    border: solid #00D4FF;
  }

  AIPanel > .reply-tone {
    color: #9945FF;
    text-style: italic;
  }

  AIPanel > .reply-preview {
    color: #666688;
  }

  AIPanel > .empty-state {
    color: #666688;
    text-align: center;
    margin-top: 3;
  }

  AIPanel > .loading {
    color: #9945FF;
    text-align: center;
    margin-top: 3;
  }

  AIPanel Button {
    width: 100%;
    margin-top: 1;
  }
  """

  def __init__(self, **kwargs):
    """Initialize AI panel."""
    super().__init__(**kwargs)
    self._current_email: Optional[Email] = None
    self._summary: Optional[EmailSummary] = None
    self._replies: List[ReplyDraft] = []
    self._loading: bool = False

  def compose(self):
    """Compose the widget."""
    yield Static(f" {ICONS['ai']} AI ASSISTANT", classes="title")
    yield VerticalScroll(id="ai-content")

  def on_mount(self) -> None:
    """Initial render."""
    self._render_empty()

  def show_loading(self, message: str = "Analyzing...") -> None:
    """Show loading state.

    Args:
      message: Loading message to display
    """
    self._loading = True
    content = self.query_one("#ai-content", VerticalScroll)
    content.remove_children()
    content.mount(Static(f"{ICONS['loading']} {message}", classes="loading"))

  def show_summary(self, summary: EmailSummary) -> None:
    """Display AI summary.

    Args:
      summary: EmailSummary to display
    """
    self._summary = summary
    self._loading = False
    self._render_summary()

  def show_replies(self, replies: List[ReplyDraft]) -> None:
    """Display smart reply suggestions.

    Args:
      replies: List of ReplyDraft suggestions
    """
    self._replies = replies
    self._render_replies()

  def clear(self) -> None:
    """Clear the panel."""
    self._current_email = None
    self._summary = None
    self._replies = []
    self._loading = False
    self._render_empty()

  def set_email(self, email: Email) -> None:
    """Set the current email context.

    Args:
      email: Email being analyzed
    """
    self._current_email = email

    # If email already has AI data, show it
    if email.ai_summary:
      self._summary = EmailSummary(
        one_liner=email.ai_summary,
        category=email.ai_category or EmailCategory.OTHER,
        sentiment=email.ai_sentiment or EmailSentiment.NEUTRAL,
        action_items=email.ai_action_items,
      )
      self._render_summary()
    else:
      self._render_empty()

  def _render_empty(self) -> None:
    """Render empty state with action buttons."""
    content = self.query_one("#ai-content", VerticalScroll)
    content.remove_children()

    if self._current_email:
      content.mount(
        Static("No AI analysis yet", classes="empty-state")
      )
      content.mount(
        Button(f"{ICONS['ai']} Summarize", id="btn-summarize", variant="primary")
      )
      content.mount(
        Button(f"{ICONS['reply']} Smart Reply", id="btn-reply", variant="default")
      )
    else:
      content.mount(
        Static("Select an email to analyze", classes="empty-state")
      )

  def _render_summary(self) -> None:
    """Render the AI summary."""
    if not self._summary:
      return

    content = self.query_one("#ai-content", VerticalScroll)
    content.remove_children()

    # One-liner summary
    content.mount(Static("Summary", classes="section-title"))
    content.mount(Static(self._summary.one_liner, classes="summary"))

    # Category and sentiment
    cat_sent = Text()
    cat_sent.append(f"{self._get_category_icon(self._summary.category)} ")
    cat_sent.append(self._summary.category.value.capitalize(), style=COLORS["muted"])
    cat_sent.append(" • ")
    cat_sent.append(
      self._get_sentiment_text(self._summary.sentiment),
      style=self._get_sentiment_color(self._summary.sentiment),
    )
    content.mount(Static(cat_sent, classes="category"))

    # Key points
    if self._summary.key_points:
      content.mount(Static("Key Points", classes="section-title"))
      for point in self._summary.key_points:
        point_text = Text()
        point_text.append("• ", style=COLORS["primary"])
        point_text.append(point)
        content.mount(Static(point_text, classes="key-point"))

    # Action items
    if self._summary.action_items:
      content.mount(Static("Action Items", classes="section-title"))
      for item in self._summary.action_items:
        item_text = Text()
        item_text.append("☐ ", style=COLORS["success"])
        item_text.append(item)
        content.mount(Static(item_text, classes="action-item"))

    # Smart reply button
    content.mount(
      Button(f"{ICONS['reply']} Smart Reply", id="btn-reply", variant="default")
    )

  def _render_replies(self) -> None:
    """Render smart reply suggestions."""
    if not self._replies:
      return

    content = self.query_one("#ai-content", VerticalScroll)

    # Add replies section
    content.mount(Static("Smart Replies", classes="section-title"))

    for i, reply in enumerate(self._replies):
      # Reply option container
      reply_container = Vertical(classes="reply-option", id=f"reply-{i}")

      # Tone label
      tone_text = Text()
      tone_text.append(f"{reply.tone.capitalize()}", style=COLORS["ai"])
      reply_container.mount(Static(tone_text, classes="reply-tone"))

      # Preview
      preview = reply.content[:100] + "..." if len(reply.content) > 100 else reply.content
      reply_container.mount(Static(preview, classes="reply-preview"))

      # Use button
      reply_container.mount(
        Button("Use This Reply", id=f"btn-use-reply-{i}", variant="primary")
      )

      content.mount(reply_container)

  def _get_category_icon(self, category: EmailCategory) -> str:
    """Get icon for category."""
    icons = {
      EmailCategory.WORK: "",
      EmailCategory.PERSONAL: "",
      EmailCategory.NEWSLETTER: "",
      EmailCategory.TRANSACTION: "",
      EmailCategory.SOCIAL: "",
      EmailCategory.SPAM: "",
      EmailCategory.OTHER: "",
    }
    return icons.get(category, "")

  def _get_sentiment_text(self, sentiment: EmailSentiment) -> str:
    """Get text for sentiment."""
    texts = {
      EmailSentiment.POSITIVE: "Positive",
      EmailSentiment.NEUTRAL: "Neutral",
      EmailSentiment.NEGATIVE: "Negative",
      EmailSentiment.URGENT: "Urgent",
    }
    return texts.get(sentiment, "Unknown")

  def _get_sentiment_color(self, sentiment: EmailSentiment) -> str:
    """Get color for sentiment."""
    colors = {
      EmailSentiment.POSITIVE: COLORS["success"],
      EmailSentiment.NEUTRAL: COLORS["muted"],
      EmailSentiment.NEGATIVE: COLORS["warning"],
      EmailSentiment.URGENT: COLORS["error"],
    }
    return colors.get(sentiment, COLORS["muted"])

  def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button presses."""
    if event.button.id == "btn-summarize":
      self.post_message(self.SummarizeRequested())
    elif event.button.id == "btn-reply":
      self.post_message(self.SmartReplyRequested())
    elif event.button.id and event.button.id.startswith("btn-use-reply-"):
      try:
        idx = int(event.button.id.split("-")[-1])
        if 0 <= idx < len(self._replies):
          self.post_message(self.ReplySelected(self._replies[idx]))
      except ValueError:
        pass
