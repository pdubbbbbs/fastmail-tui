"""Fastmail Masked Email management."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Any
import asyncio

from jmapc.fastmail import MaskedEmailGet, MaskedEmailSet


@dataclass
class MaskedEmail:
  """Fastmail masked email alias.

  Masked emails are unique email addresses that forward to your
  main inbox, useful for signups and privacy.
  """
  id: str
  email: str
  state: str  # "enabled", "disabled", "deleted", "pending"
  for_domain: Optional[str] = None
  description: str = ""
  created_at: Optional[datetime] = None
  last_message_at: Optional[datetime] = None
  url: Optional[str] = None

  @property
  def is_active(self) -> bool:
    """Check if masked email is active."""
    return self.state == "enabled"

  @property
  def is_disabled(self) -> bool:
    """Check if masked email is disabled."""
    return self.state == "disabled"

  @property
  def status_icon(self) -> str:
    """Get status icon."""
    if self.is_active:
      return ""
    elif self.is_disabled:
      return ""
    else:
      return ""

  @property
  def status_display(self) -> str:
    """Get human-readable status."""
    return self.state.capitalize()

  @property
  def domain_display(self) -> str:
    """Get domain display text."""
    return self.for_domain or "General"

  @property
  def description_display(self) -> str:
    """Get description or placeholder."""
    return self.description or "(no description)"

  @property
  def last_used_display(self) -> str:
    """Get human-readable last message date."""
    if not self.last_message_at:
      return "Never"

    now = datetime.now()
    diff = now - self.last_message_at

    if diff.days == 0:
      return "Today"
    elif diff.days == 1:
      return "Yesterday"
    elif diff.days < 7:
      return f"{diff.days} days ago"
    elif diff.days < 30:
      weeks = diff.days // 7
      return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif diff.days < 365:
      months = diff.days // 30
      return f"{months} month{'s' if months > 1 else ''} ago"
    else:
      return self.last_message_at.strftime("%b %Y")

  @classmethod
  def from_jmap(cls, data: Any) -> "MaskedEmail":
    """Create from jmapc MaskedEmail object."""
    created_at = None
    if hasattr(data, "created_at") and data.created_at:
      created_at = data.created_at

    last_message_at = None
    if hasattr(data, "last_message_at") and data.last_message_at:
      last_message_at = data.last_message_at

    return cls(
      id=data.id,
      email=getattr(data, "email", ""),
      state=getattr(data, "state", "enabled"),
      for_domain=getattr(data, "for_domain", None),
      description=getattr(data, "description", "") or "",
      created_at=created_at,
      last_message_at=last_message_at,
      url=getattr(data, "url", None),
    )


class MaskedEmailManager:
  """Manage Fastmail masked email aliases.

  Provides methods to list, create, toggle, and delete masked emails.
  """

  def __init__(self, client: Any):
    """Initialize manager.

    Args:
      client: jmapc Client instance
    """
    self.client = client

  async def list_all(self) -> List[MaskedEmail]:
    """Get all masked emails.

    Returns:
      List of MaskedEmail objects sorted by creation date (newest first)
    """
    loop = asyncio.get_event_loop()

    def _list():
      try:
        result = self.client.request(MaskedEmailGet())
        return result.data if result else []
      except Exception:
        return []

    jmap_masked = await loop.run_in_executor(None, _list)

    masked_emails = [MaskedEmail.from_jmap(m) for m in jmap_masked]

    # Sort by creation date, newest first
    return sorted(
      masked_emails,
      key=lambda m: m.created_at or datetime.min,
      reverse=True,
    )

  async def get_active(self) -> List[MaskedEmail]:
    """Get only active (enabled) masked emails."""
    all_masked = await self.list_all()
    return [m for m in all_masked if m.is_active]

  async def get_by_domain(self, domain: str) -> List[MaskedEmail]:
    """Get masked emails for a specific domain."""
    all_masked = await self.list_all()
    return [m for m in all_masked if m.for_domain == domain]

  async def create(
    self,
    for_domain: Optional[str] = None,
    description: str = "",
  ) -> MaskedEmail:
    """Create a new masked email address.

    Args:
      for_domain: Domain this masked email is for (optional)
      description: Description of the masked email (optional)

    Returns:
      The newly created MaskedEmail
    """
    loop = asyncio.get_event_loop()

    def _create():
      create_data = {
        "state": "enabled",
      }
      if for_domain:
        create_data["forDomain"] = for_domain
      if description:
        create_data["description"] = description

      result = self.client.request(
        MaskedEmailSet(create={"new": create_data})
      )

      if result and result.created and "new" in result.created:
        return result.created["new"]
      return None

    created = await loop.run_in_executor(None, _create)

    if not created:
      raise RuntimeError("Failed to create masked email")

    return MaskedEmail.from_jmap(created)

  async def enable(self, masked_email_id: str) -> None:
    """Enable a masked email."""
    await self._set_state(masked_email_id, "enabled")

  async def disable(self, masked_email_id: str) -> None:
    """Disable a masked email (stops forwarding)."""
    await self._set_state(masked_email_id, "disabled")

  async def toggle(self, masked_email_id: str, current_state: str) -> str:
    """Toggle masked email state.

    Args:
      masked_email_id: ID of masked email
      current_state: Current state ("enabled" or "disabled")

    Returns:
      New state after toggle
    """
    new_state = "disabled" if current_state == "enabled" else "enabled"
    await self._set_state(masked_email_id, new_state)
    return new_state

  async def _set_state(self, masked_email_id: str, state: str) -> None:
    """Set the state of a masked email."""
    loop = asyncio.get_event_loop()

    def _update():
      self.client.request(
        MaskedEmailSet(update={masked_email_id: {"state": state}})
      )

    await loop.run_in_executor(None, _update)

  async def update_description(
    self,
    masked_email_id: str,
    description: str,
  ) -> None:
    """Update the description of a masked email."""
    loop = asyncio.get_event_loop()

    def _update():
      self.client.request(
        MaskedEmailSet(update={masked_email_id: {"description": description}})
      )

    await loop.run_in_executor(None, _update)

  async def delete(self, masked_email_id: str) -> None:
    """Permanently delete a masked email.

    Warning: This cannot be undone. The email address will be released
    and could potentially be assigned to someone else.
    """
    loop = asyncio.get_event_loop()

    def _delete():
      self.client.request(MaskedEmailSet(destroy=[masked_email_id]))

    await loop.run_in_executor(None, _delete)
