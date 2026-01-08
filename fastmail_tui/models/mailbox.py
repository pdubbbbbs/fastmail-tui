"""Mailbox data models."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Mailbox:
  """Email mailbox/folder."""
  id: str
  name: str
  role: Optional[str] = None  # inbox, sent, drafts, trash, archive, spam, etc.
  parent_id: Optional[str] = None
  sort_order: int = 0
  total_emails: int = 0
  unread_emails: int = 0
  total_threads: int = 0
  unread_threads: int = 0
  is_subscribed: bool = True

  @property
  def is_system(self) -> bool:
    """Check if this is a system mailbox (has a role)."""
    return self.role is not None

  @property
  def display_name(self) -> str:
    """Get display name (role-based name or actual name)."""
    role_names = {
      "inbox": "Inbox",
      "sent": "Sent",
      "drafts": "Drafts",
      "trash": "Trash",
      "archive": "Archive",
      "spam": "Spam",
      "junk": "Junk",
    }
    if self.role and self.role.lower() in role_names:
      return role_names[self.role.lower()]
    return self.name

  @property
  def icon(self) -> str:
    """Get icon for the mailbox."""
    from ..theme import ICONS

    role_icons = {
      "inbox": ICONS["inbox"],
      "sent": ICONS["sent"],
      "drafts": ICONS["drafts"],
      "trash": ICONS["trash"],
      "archive": ICONS["archive"],
      "spam": ICONS["spam"],
      "junk": ICONS["spam"],
    }
    if self.role and self.role.lower() in role_icons:
      return role_icons[self.role.lower()]
    return ICONS["folder"]

  @property
  def unread_display(self) -> str:
    """Get unread count display."""
    if self.unread_emails > 0:
      if self.unread_emails > 999:
        return "999+"
      return str(self.unread_emails)
    return ""

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    return {
      "id": self.id,
      "name": self.name,
      "role": self.role,
      "parent_id": self.parent_id,
      "sort_order": self.sort_order,
      "total_emails": self.total_emails,
      "unread_emails": self.unread_emails,
      "total_threads": self.total_threads,
      "unread_threads": self.unread_threads,
      "is_subscribed": self.is_subscribed,
    }

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> "Mailbox":
    """Create from dictionary."""
    return cls(
      id=data["id"],
      name=data["name"],
      role=data.get("role"),
      parent_id=data.get("parent_id"),
      sort_order=data.get("sort_order", 0),
      total_emails=data.get("total_emails", 0),
      unread_emails=data.get("unread_emails", 0),
      total_threads=data.get("total_threads", 0),
      unread_threads=data.get("unread_threads", 0),
      is_subscribed=data.get("is_subscribed", True),
    )

  @classmethod
  def from_jmap(cls, data: Any) -> "Mailbox":
    """Create from jmapc Mailbox object."""
    return cls(
      id=data.id,
      name=data.name,
      role=getattr(data, "role", None),
      parent_id=getattr(data, "parent_id", None),
      sort_order=getattr(data, "sort_order", 0) or 0,
      total_emails=getattr(data, "total_emails", 0) or 0,
      unread_emails=getattr(data, "unread_emails", 0) or 0,
      total_threads=getattr(data, "total_threads", 0) or 0,
      unread_threads=getattr(data, "unread_threads", 0) or 0,
      is_subscribed=getattr(data, "is_subscribed", True),
    )


def sort_mailboxes(mailboxes: list[Mailbox]) -> list[Mailbox]:
  """Sort mailboxes with system folders first in standard order."""
  role_order = {
    "inbox": 0,
    "drafts": 1,
    "sent": 2,
    "archive": 3,
    "spam": 4,
    "junk": 4,
    "trash": 5,
  }

  def sort_key(m: Mailbox) -> tuple:
    if m.role:
      return (0, role_order.get(m.role.lower(), 99), m.name.lower())
    return (1, m.sort_order, m.name.lower())

  return sorted(mailboxes, key=sort_key)
