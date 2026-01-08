"""Email compose modal."""

from typing import Optional, List
from dataclasses import dataclass
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Button, Static
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from rich.text import Text

from ...models.email import Email
from ...theme import COLORS, ICONS


@dataclass
class ComposedEmail:
  """Data for a composed email."""
  to: str
  cc: str
  subject: str
  body: str
  in_reply_to: Optional[str] = None  # Email ID if replying


class ComposeModal(ModalScreen[Optional[ComposedEmail]]):
  """Modal screen for composing emails.

  Returns ComposedEmail or None if cancelled.
  """

  BINDINGS = [
    Binding("escape", "cancel", "Cancel", show=True),
    Binding("ctrl+enter", "send", "Send", show=True),
    Binding("ctrl+s", "send", "Send", show=False),
  ]

  DEFAULT_CSS = """
  ComposeModal {
    align: center middle;
  }

  ComposeModal > Vertical {
    width: 80%;
    max-width: 100;
    height: 80%;
    background: #12121A;
    border: solid #00D4FF;
    padding: 1;
  }

  ComposeModal .title {
    color: #00D4FF;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
  }

  ComposeModal .field-label {
    color: #666688;
    margin-top: 1;
  }

  ComposeModal Input {
    margin-bottom: 0;
  }

  ComposeModal TextArea {
    height: 1fr;
    margin-top: 1;
  }

  ComposeModal .button-row {
    height: 3;
    margin-top: 1;
    align: right middle;
  }

  ComposeModal Button {
    margin-left: 1;
  }
  """

  def __init__(
    self,
    reply_to: Optional[Email] = None,
    reply_all: bool = False,
    forward: bool = False,
    draft_body: Optional[str] = None,
    **kwargs,
  ):
    """Initialize compose modal.

    Args:
      reply_to: Email being replied to (if any)
      reply_all: Whether this is a reply-all
      forward: Whether this is a forward
      draft_body: Pre-filled body content
    """
    super().__init__(**kwargs)
    self._reply_to = reply_to
    self._reply_all = reply_all
    self._forward = forward
    self._draft_body = draft_body

  def compose(self):
    """Compose the modal."""
    # Determine title
    if self._forward:
      title = f"{ICONS['forward']} Forward Email"
    elif self._reply_to:
      title = f"{ICONS['reply']} Reply" + (" All" if self._reply_all else "")
    else:
      title = f"{ICONS['compose']} New Email"

    with Vertical():
      yield Static(f" {title}", classes="title")

      yield Static("To:", classes="field-label")
      yield Input(
        placeholder="recipient@example.com",
        id="input-to",
        value=self._get_initial_to(),
      )

      yield Static("CC:", classes="field-label")
      yield Input(
        placeholder="cc@example.com (optional)",
        id="input-cc",
        value=self._get_initial_cc(),
      )

      yield Static("Subject:", classes="field-label")
      yield Input(
        placeholder="Subject",
        id="input-subject",
        value=self._get_initial_subject(),
      )

      yield TextArea(
        self._get_initial_body(),
        id="input-body",
      )

      with Horizontal(classes="button-row"):
        yield Button("Cancel", id="btn-cancel", variant="default")
        yield Button(f"{ICONS['sent']} Send", id="btn-send", variant="primary")

  def on_mount(self) -> None:
    """Focus appropriate field on mount."""
    if self._reply_to:
      # Focus body for replies
      self.query_one("#input-body", TextArea).focus()
    else:
      # Focus To for new emails
      self.query_one("#input-to", Input).focus()

  def _get_initial_to(self) -> str:
    """Get initial To field value."""
    if self._reply_to and not self._forward:
      # Reply to sender
      return self._reply_to.from_email
    return ""

  def _get_initial_cc(self) -> str:
    """Get initial CC field value."""
    if self._reply_all and self._reply_to:
      # Include other recipients in CC
      others = []
      for addr in self._reply_to.to_addresses:
        if addr.email != self._reply_to.from_email:
          others.append(addr.email)
      for addr in self._reply_to.cc_addresses:
        others.append(addr.email)
      return ", ".join(others[:5])  # Limit
    return ""

  def _get_initial_subject(self) -> str:
    """Get initial subject."""
    if self._reply_to:
      subject = self._reply_to.subject
      if self._forward:
        if not subject.lower().startswith("fwd:"):
          return f"Fwd: {subject}"
      else:
        if not subject.lower().startswith("re:"):
          return f"Re: {subject}"
      return subject
    return ""

  def _get_initial_body(self) -> str:
    """Get initial body content."""
    if self._draft_body:
      return self._draft_body

    if self._reply_to:
      # Quote original message
      quote_header = f"\n\nOn {self._reply_to.date_display}, {self._reply_to.from_display} wrote:\n"
      original = self._reply_to.body_text or self._reply_to.preview
      quoted = "\n".join(f"> {line}" for line in original.split("\n")[:20])
      return f"\n{quote_header}{quoted}"

    return ""

  def action_cancel(self) -> None:
    """Cancel composition."""
    self.dismiss(None)

  def action_send(self) -> None:
    """Send the email."""
    to_input = self.query_one("#input-to", Input)
    cc_input = self.query_one("#input-cc", Input)
    subject_input = self.query_one("#input-subject", Input)
    body_input = self.query_one("#input-body", TextArea)

    to = to_input.value.strip()
    if not to:
      self.notify("To address is required", severity="error")
      to_input.focus()
      return

    composed = ComposedEmail(
      to=to,
      cc=cc_input.value.strip(),
      subject=subject_input.value.strip() or "(no subject)",
      body=body_input.text,
      in_reply_to=self._reply_to.id if self._reply_to and not self._forward else None,
    )

    self.dismiss(composed)

  def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button presses."""
    if event.button.id == "btn-cancel":
      self.action_cancel()
    elif event.button.id == "btn-send":
      self.action_send()
