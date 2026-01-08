"""Email data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class EmailCategory(str, Enum):
  """AI-detected email categories."""
  WORK = "work"
  PERSONAL = "personal"
  NEWSLETTER = "newsletter"
  TRANSACTION = "transaction"
  SOCIAL = "social"
  SPAM = "spam"
  OTHER = "other"


class EmailSentiment(str, Enum):
  """AI-detected email sentiment."""
  POSITIVE = "positive"
  NEUTRAL = "neutral"
  NEGATIVE = "negative"
  URGENT = "urgent"


@dataclass
class EmailAddress:
  """Email address with optional display name."""
  email: str
  name: Optional[str] = None

  @property
  def display(self) -> str:
    """Get display string for the address."""
    if self.name:
      return f"{self.name} <{self.email}>"
    return self.email

  @property
  def short_display(self) -> str:
    """Get short display (name only if available)."""
    return self.name or self.email.split("@")[0]

  @classmethod
  def from_jmap(cls, data: Dict[str, Any]) -> "EmailAddress":
    """Create from JMAP address object."""
    return cls(
      email=data.get("email", ""),
      name=data.get("name"),
    )


@dataclass
class Attachment:
  """Email attachment."""
  id: str
  name: str
  type: str
  size: int
  is_inline: bool = False

  @property
  def size_display(self) -> str:
    """Human-readable file size."""
    if self.size < 1024:
      return f"{self.size} B"
    elif self.size < 1024 * 1024:
      return f"{self.size / 1024:.1f} KB"
    else:
      return f"{self.size / (1024 * 1024):.1f} MB"

  @classmethod
  def from_jmap(cls, attachment_id: str, data: Dict[str, Any]) -> "Attachment":
    """Create from JMAP attachment object."""
    return cls(
      id=attachment_id,
      name=data.get("name", "attachment"),
      type=data.get("type", "application/octet-stream"),
      size=data.get("size", 0),
      is_inline=data.get("disposition", "attachment") == "inline",
    )


@dataclass
class Email:
  """Email message."""
  id: str
  thread_id: str
  mailbox_ids: Dict[str, bool]
  subject: str
  preview: str
  received_at: datetime
  sent_at: Optional[datetime] = None
  from_addresses: list[EmailAddress] = field(default_factory=list)
  to_addresses: list[EmailAddress] = field(default_factory=list)
  cc_addresses: list[EmailAddress] = field(default_factory=list)
  bcc_addresses: list[EmailAddress] = field(default_factory=list)
  reply_to: list[EmailAddress] = field(default_factory=list)
  keywords: Dict[str, bool] = field(default_factory=dict)
  size: int = 0
  has_attachment: bool = False
  attachments: list[Attachment] = field(default_factory=list)
  body_text: Optional[str] = None
  body_html: Optional[str] = None

  # AI-generated fields (populated later)
  ai_summary: Optional[str] = None
  ai_category: Optional[EmailCategory] = None
  ai_sentiment: Optional[EmailSentiment] = None
  ai_action_items: list[str] = field(default_factory=list)

  @property
  def is_unread(self) -> bool:
    """Check if email is unread."""
    return not self.keywords.get("$seen", False)

  @property
  def is_starred(self) -> bool:
    """Check if email is starred/flagged."""
    return self.keywords.get("$flagged", False)

  @property
  def is_draft(self) -> bool:
    """Check if email is a draft."""
    return self.keywords.get("$draft", False)

  @property
  def is_answered(self) -> bool:
    """Check if email has been replied to."""
    return self.keywords.get("$answered", False)

  @property
  def from_display(self) -> str:
    """Get display name for sender."""
    if self.from_addresses:
      return self.from_addresses[0].short_display
    return "Unknown"

  @property
  def from_email(self) -> str:
    """Get email address of sender."""
    if self.from_addresses:
      return self.from_addresses[0].email
    return ""

  @property
  def to_display(self) -> str:
    """Get display names for recipients."""
    if not self.to_addresses:
      return ""
    if len(self.to_addresses) == 1:
      return self.to_addresses[0].short_display
    return f"{self.to_addresses[0].short_display} +{len(self.to_addresses) - 1}"

  @property
  def relative_date(self) -> str:
    """Get human-readable relative date."""
    now = datetime.now()
    diff = now - self.received_at

    if diff.days == 0:
      if diff.seconds < 60:
        return "now"
      elif diff.seconds < 3600:
        mins = diff.seconds // 60
        return f"{mins}m"
      else:
        hours = diff.seconds // 3600
        return f"{hours}h"
    elif diff.days == 1:
      return "yesterday"
    elif diff.days < 7:
      return self.received_at.strftime("%a")
    elif diff.days < 365:
      return self.received_at.strftime("%b %d")
    else:
      return self.received_at.strftime("%Y")

  @property
  def date_display(self) -> str:
    """Get formatted date string."""
    return self.received_at.strftime("%b %d, %Y %I:%M %p")

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary for caching."""
    return {
      "id": self.id,
      "thread_id": self.thread_id,
      "mailbox_ids": self.mailbox_ids,
      "subject": self.subject,
      "preview": self.preview,
      "received_at": self.received_at.isoformat(),
      "sent_at": self.sent_at.isoformat() if self.sent_at else None,
      "from_addresses": [{"email": a.email, "name": a.name} for a in self.from_addresses],
      "to_addresses": [{"email": a.email, "name": a.name} for a in self.to_addresses],
      "cc_addresses": [{"email": a.email, "name": a.name} for a in self.cc_addresses],
      "keywords": self.keywords,
      "size": self.size,
      "has_attachment": self.has_attachment,
      "body_text": self.body_text,
      "body_html": self.body_html,
      "ai_summary": self.ai_summary,
      "ai_category": self.ai_category.value if self.ai_category else None,
      "ai_sentiment": self.ai_sentiment.value if self.ai_sentiment else None,
      "ai_action_items": self.ai_action_items,
    }

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> "Email":
    """Create from dictionary (cached data)."""
    return cls(
      id=data["id"],
      thread_id=data["thread_id"],
      mailbox_ids=data["mailbox_ids"],
      subject=data["subject"],
      preview=data["preview"],
      received_at=datetime.fromisoformat(data["received_at"]),
      sent_at=datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None,
      from_addresses=[EmailAddress(**a) for a in data.get("from_addresses", [])],
      to_addresses=[EmailAddress(**a) for a in data.get("to_addresses", [])],
      cc_addresses=[EmailAddress(**a) for a in data.get("cc_addresses", [])],
      keywords=data.get("keywords", {}),
      size=data.get("size", 0),
      has_attachment=data.get("has_attachment", False),
      body_text=data.get("body_text"),
      body_html=data.get("body_html"),
      ai_summary=data.get("ai_summary"),
      ai_category=EmailCategory(data["ai_category"]) if data.get("ai_category") else None,
      ai_sentiment=EmailSentiment(data["ai_sentiment"]) if data.get("ai_sentiment") else None,
      ai_action_items=data.get("ai_action_items", []),
    )

  @classmethod
  def from_jmap(cls, data: Any) -> "Email":
    """Create from jmapc Email object."""
    # Handle jmapc Email object attributes
    from_addrs = []
    if hasattr(data, "mail_from") and data.mail_from:
      for addr in data.mail_from:
        from_addrs.append(EmailAddress(email=addr.email, name=addr.name))

    to_addrs = []
    if hasattr(data, "to") and data.to:
      for addr in data.to:
        to_addrs.append(EmailAddress(email=addr.email, name=addr.name))

    cc_addrs = []
    if hasattr(data, "cc") and data.cc:
      for addr in data.cc:
        cc_addrs.append(EmailAddress(email=addr.email, name=addr.name))

    # Parse keywords
    keywords = {}
    if hasattr(data, "keywords") and data.keywords:
      keywords = dict(data.keywords)

    # Parse received date
    received_at = datetime.now()
    if hasattr(data, "received_at") and data.received_at:
      received_at = data.received_at

    sent_at = None
    if hasattr(data, "sent_at") and data.sent_at:
      sent_at = data.sent_at

    # Parse mailbox IDs
    mailbox_ids = {}
    if hasattr(data, "mailbox_ids") and data.mailbox_ids:
      mailbox_ids = dict(data.mailbox_ids)

    return cls(
      id=data.id,
      thread_id=getattr(data, "thread_id", data.id),
      mailbox_ids=mailbox_ids,
      subject=getattr(data, "subject", "(no subject)") or "(no subject)",
      preview=getattr(data, "preview", "")[:200] if hasattr(data, "preview") else "",
      received_at=received_at,
      sent_at=sent_at,
      from_addresses=from_addrs,
      to_addresses=to_addrs,
      cc_addresses=cc_addrs,
      keywords=keywords,
      size=getattr(data, "size", 0) or 0,
      has_attachment=getattr(data, "has_attachment", False) or False,
    )
