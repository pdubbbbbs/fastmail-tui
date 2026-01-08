"""JMAP client wrapper using jmapc library."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import asyncio
from functools import partial

from jmapc import Client
from jmapc.methods import (
  EmailGet,
  EmailQuery,
  EmailSet,
  MailboxGet,
  MailboxQuery,
  ThreadGet,
  IdentityGet,
)

from ..models.email import Email
from ..models.mailbox import Mailbox, sort_mailboxes


@dataclass
class JMAPSession:
  """JMAP session with account info."""
  client: Client
  account_id: str
  primary_email: str
  capabilities: Dict[str, Any]


class FastmailClient:
  """Async-friendly Fastmail JMAP client.

  Wraps the jmapc library with async support and convenient methods
  for common email operations.
  """

  def __init__(self, host: str, token: str):
    """Initialize client.

    Args:
      host: JMAP server hostname (e.g., api.fastmail.com)
      token: API token from Fastmail settings
    """
    self.host = host
    self.token = token
    self._session: Optional[JMAPSession] = None
    self._mailboxes_cache: Dict[str, Mailbox] = {}

  @property
  def is_connected(self) -> bool:
    """Check if connected to server."""
    return self._session is not None

  @property
  def account_id(self) -> Optional[str]:
    """Get current account ID."""
    return self._session.account_id if self._session else None

  @property
  def primary_email(self) -> Optional[str]:
    """Get primary email address."""
    return self._session.primary_email if self._session else None

  async def connect(self) -> JMAPSession:
    """Establish JMAP session.

    Returns:
      JMAPSession with client and account info
    """
    loop = asyncio.get_event_loop()

    # jmapc is synchronous, run in executor
    def _connect():
      client = Client.create_with_api_token(
        host=self.host,
        api_token=self.token
      )
      return client

    client = await loop.run_in_executor(None, _connect)

    # Get primary identity for email address
    def _get_identity():
      try:
        result = client.request(IdentityGet())
        if result and result.data:
          return result.data[0].email
      except Exception:
        pass
      return ""

    primary_email = await loop.run_in_executor(None, _get_identity)

    self._session = JMAPSession(
      client=client,
      account_id=client.account_id,
      primary_email=primary_email,
      capabilities=client.session.capabilities if hasattr(client, 'session') else {},
    )

    return self._session

  async def disconnect(self) -> None:
    """Disconnect from server."""
    self._session = None
    self._mailboxes_cache.clear()

  async def get_mailboxes(self, force_refresh: bool = False) -> List[Mailbox]:
    """Fetch all mailboxes.

    Args:
      force_refresh: Force refresh from server, ignoring cache

    Returns:
      List of Mailbox objects, sorted appropriately
    """
    if not self._session:
      raise RuntimeError("Not connected")

    if not force_refresh and self._mailboxes_cache:
      return sort_mailboxes(list(self._mailboxes_cache.values()))

    loop = asyncio.get_event_loop()

    def _get_mailboxes():
      result = self._session.client.request(MailboxGet())
      return result.data if result else []

    jmap_mailboxes = await loop.run_in_executor(None, _get_mailboxes)

    self._mailboxes_cache.clear()
    mailboxes = []
    for m in jmap_mailboxes:
      mailbox = Mailbox.from_jmap(m)
      self._mailboxes_cache[mailbox.id] = mailbox
      mailboxes.append(mailbox)

    return sort_mailboxes(mailboxes)

  def get_mailbox_by_role(self, role: str) -> Optional[Mailbox]:
    """Get a mailbox by its role (inbox, sent, trash, etc.)."""
    for mailbox in self._mailboxes_cache.values():
      if mailbox.role and mailbox.role.lower() == role.lower():
        return mailbox
    return None

  def get_mailbox_by_id(self, mailbox_id: str) -> Optional[Mailbox]:
    """Get a mailbox by its ID."""
    return self._mailboxes_cache.get(mailbox_id)

  async def get_emails(
    self,
    mailbox_id: Optional[str] = None,
    limit: int = 50,
    position: int = 0,
    filter_query: Optional[Dict[str, Any]] = None,
  ) -> List[Email]:
    """Fetch emails from a mailbox or with filter.

    Args:
      mailbox_id: Mailbox to fetch from (default: inbox)
      limit: Maximum emails to fetch
      position: Offset for pagination
      filter_query: Additional JMAP filter conditions

    Returns:
      List of Email objects
    """
    if not self._session:
      raise RuntimeError("Not connected")

    # Default to inbox if no mailbox specified
    if mailbox_id is None:
      inbox = self.get_mailbox_by_role("inbox")
      if inbox:
        mailbox_id = inbox.id

    # Build filter
    email_filter: Dict[str, Any] = {}
    if mailbox_id:
      email_filter["inMailbox"] = mailbox_id
    if filter_query:
      email_filter.update(filter_query)

    loop = asyncio.get_event_loop()

    def _query_and_get():
      # Query for email IDs
      query_result = self._session.client.request(
        EmailQuery(
          filter=email_filter if email_filter else None,
          sort=[{"property": "receivedAt", "isAscending": False}],
          limit=limit,
          position=position,
        )
      )

      if not query_result or not query_result.ids:
        return []

      # Fetch email details
      emails_result = self._session.client.request(
        EmailGet(
          ids=query_result.ids,
          properties=[
            "id",
            "threadId",
            "mailboxIds",
            "from",
            "to",
            "cc",
            "bcc",
            "replyTo",
            "subject",
            "receivedAt",
            "sentAt",
            "preview",
            "hasAttachment",
            "keywords",
            "size",
          ],
        )
      )

      return emails_result.data if emails_result else []

    jmap_emails = await loop.run_in_executor(None, _query_and_get)

    return [Email.from_jmap(e) for e in jmap_emails]

  async def get_email_by_id(self, email_id: str, fetch_body: bool = True) -> Optional[Email]:
    """Fetch a single email by ID with full content.

    Args:
      email_id: Email ID to fetch
      fetch_body: Whether to fetch body content

    Returns:
      Email object or None if not found
    """
    if not self._session:
      raise RuntimeError("Not connected")

    loop = asyncio.get_event_loop()

    properties = [
      "id",
      "threadId",
      "mailboxIds",
      "from",
      "to",
      "cc",
      "bcc",
      "replyTo",
      "subject",
      "receivedAt",
      "sentAt",
      "preview",
      "hasAttachment",
      "keywords",
      "size",
    ]

    if fetch_body:
      properties.extend(["bodyValues", "textBody", "htmlBody"])

    def _get_email():
      result = self._session.client.request(
        EmailGet(
          ids=[email_id],
          properties=properties,
          fetchTextBodyValues=fetch_body,
          fetchHTMLBodyValues=fetch_body,
        )
      )
      return result.data[0] if result and result.data else None

    jmap_email = await loop.run_in_executor(None, _get_email)

    if not jmap_email:
      return None

    email = Email.from_jmap(jmap_email)

    # Extract body content if fetched
    if fetch_body and hasattr(jmap_email, "body_values"):
      body_values = jmap_email.body_values or {}

      # Get text body
      if hasattr(jmap_email, "text_body") and jmap_email.text_body:
        for part in jmap_email.text_body:
          part_id = part.part_id if hasattr(part, "part_id") else None
          if part_id and part_id in body_values:
            email.body_text = body_values[part_id].value
            break

      # Get HTML body
      if hasattr(jmap_email, "html_body") and jmap_email.html_body:
        for part in jmap_email.html_body:
          part_id = part.part_id if hasattr(part, "part_id") else None
          if part_id and part_id in body_values:
            email.body_html = body_values[part_id].value
            break

    return email

  async def search_emails(
    self,
    query: str,
    limit: int = 50,
    mailbox_id: Optional[str] = None,
  ) -> List[Email]:
    """Search emails with text query.

    Args:
      query: Search text
      limit: Maximum results
      mailbox_id: Limit search to specific mailbox

    Returns:
      List of matching Email objects
    """
    filter_query: Dict[str, Any] = {"text": query}
    if mailbox_id:
      filter_query["inMailbox"] = mailbox_id

    return await self.get_emails(
      mailbox_id=None,  # Don't add again
      limit=limit,
      filter_query=filter_query,
    )

  async def mark_read(self, email_ids: List[str]) -> None:
    """Mark emails as read."""
    await self._update_keywords(email_ids, {"$seen": True})

  async def mark_unread(self, email_ids: List[str]) -> None:
    """Mark emails as unread."""
    await self._update_keywords(email_ids, {"$seen": None})  # None removes keyword

  async def star(self, email_ids: List[str]) -> None:
    """Star/flag emails."""
    await self._update_keywords(email_ids, {"$flagged": True})

  async def unstar(self, email_ids: List[str]) -> None:
    """Unstar/unflag emails."""
    await self._update_keywords(email_ids, {"$flagged": None})

  async def _update_keywords(
    self,
    email_ids: List[str],
    keyword_updates: Dict[str, Optional[bool]],
  ) -> None:
    """Update keywords on emails."""
    if not self._session:
      raise RuntimeError("Not connected")

    if not email_ids:
      return

    loop = asyncio.get_event_loop()

    def _update():
      updates = {}
      for email_id in email_ids:
        updates[email_id] = {"keywords": keyword_updates}

      self._session.client.request(EmailSet(update=updates))

    await loop.run_in_executor(None, _update)

  async def move_to_mailbox(
    self,
    email_ids: List[str],
    target_mailbox_id: str,
  ) -> None:
    """Move emails to a specific mailbox."""
    if not self._session:
      raise RuntimeError("Not connected")

    if not email_ids:
      return

    loop = asyncio.get_event_loop()

    def _move():
      updates = {}
      for email_id in email_ids:
        updates[email_id] = {"mailboxIds": {target_mailbox_id: True}}

      self._session.client.request(EmailSet(update=updates))

    await loop.run_in_executor(None, _move)

  async def move_to_trash(self, email_ids: List[str]) -> None:
    """Move emails to trash."""
    trash = self.get_mailbox_by_role("trash")
    if trash:
      await self.move_to_mailbox(email_ids, trash.id)

  async def archive(self, email_ids: List[str]) -> None:
    """Archive emails."""
    archive = self.get_mailbox_by_role("archive")
    if archive:
      await self.move_to_mailbox(email_ids, archive.id)

  async def move_to_spam(self, email_ids: List[str]) -> None:
    """Move emails to spam."""
    spam = self.get_mailbox_by_role("spam") or self.get_mailbox_by_role("junk")
    if spam:
      await self.move_to_mailbox(email_ids, spam.id)

  async def delete_permanently(self, email_ids: List[str]) -> None:
    """Permanently delete emails."""
    if not self._session:
      raise RuntimeError("Not connected")

    if not email_ids:
      return

    loop = asyncio.get_event_loop()

    def _delete():
      self._session.client.request(EmailSet(destroy=email_ids))

    await loop.run_in_executor(None, _delete)

  async def get_thread(self, thread_id: str) -> List[Email]:
    """Get all emails in a thread.

    Args:
      thread_id: Thread ID to fetch

    Returns:
      List of Email objects in the thread, sorted by date
    """
    if not self._session:
      raise RuntimeError("Not connected")

    loop = asyncio.get_event_loop()

    def _get_thread():
      # Get thread info
      thread_result = self._session.client.request(
        ThreadGet(ids=[thread_id])
      )

      if not thread_result or not thread_result.data:
        return []

      thread = thread_result.data[0]
      email_ids = thread.email_ids if hasattr(thread, "email_ids") else []

      if not email_ids:
        return []

      # Get emails
      emails_result = self._session.client.request(
        EmailGet(
          ids=email_ids,
          properties=[
            "id",
            "threadId",
            "mailboxIds",
            "from",
            "to",
            "cc",
            "subject",
            "receivedAt",
            "sentAt",
            "preview",
            "hasAttachment",
            "keywords",
            "size",
          ],
        )
      )

      return emails_result.data if emails_result else []

    jmap_emails = await loop.run_in_executor(None, _get_thread)

    emails = [Email.from_jmap(e) for e in jmap_emails]
    return sorted(emails, key=lambda e: e.received_at)
