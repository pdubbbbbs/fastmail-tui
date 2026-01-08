"""Claude AI integration for email intelligence."""

from dataclasses import dataclass, field
from typing import List, Optional
import json
import asyncio

from anthropic import Anthropic

from ..models.email import EmailCategory, EmailSentiment


@dataclass
class EmailSummary:
  """AI-generated email summary."""
  one_liner: str
  key_points: List[str] = field(default_factory=list)
  action_items: List[str] = field(default_factory=list)
  sentiment: EmailSentiment = EmailSentiment.NEUTRAL
  category: EmailCategory = EmailCategory.OTHER

  @classmethod
  def from_json(cls, json_str: str) -> "EmailSummary":
    """Parse from JSON response."""
    try:
      data = json.loads(json_str)
      return cls(
        one_liner=data.get("one_liner", ""),
        key_points=data.get("key_points", []),
        action_items=data.get("action_items", []),
        sentiment=EmailSentiment(data.get("sentiment", "neutral")),
        category=EmailCategory(data.get("category", "other")),
      )
    except (json.JSONDecodeError, ValueError):
      return cls(one_liner="Failed to parse summary")


@dataclass
class ReplyDraft:
  """AI-suggested reply."""
  tone: str  # "formal", "casual", "brief"
  subject: str
  content: str
  confidence: float = 0.8

  @classmethod
  def from_dict(cls, data: dict) -> "ReplyDraft":
    """Create from dictionary."""
    return cls(
      tone=data.get("tone", "formal"),
      subject=data.get("subject", "Re: "),
      content=data.get("content", ""),
      confidence=data.get("confidence", 0.8),
    )


class ClaudeEmailAssistant:
  """Claude AI integration for email intelligence.

  Provides email summarization, smart reply suggestions,
  categorization, and thread analysis.
  """

  def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
    """Initialize assistant.

    Args:
      api_key: Anthropic API key
      model: Model to use (default: claude-sonnet-4-5)
    """
    self.client = Anthropic(api_key=api_key)
    self.model = model

  async def summarize_email(
    self,
    subject: str,
    content: str,
    max_tokens: int = 500,
  ) -> EmailSummary:
    """Generate a concise summary of an email.

    Args:
      subject: Email subject
      content: Email body content
      max_tokens: Maximum response tokens

    Returns:
      EmailSummary with analysis
    """
    loop = asyncio.get_event_loop()

    prompt = f"""Analyze this email and provide a JSON response with:
- "one_liner": A single sentence summary (max 100 chars)
- "key_points": Array of 2-3 key points
- "action_items": Array of any action items or requests
- "sentiment": One of "positive", "neutral", "negative", "urgent"
- "category": One of "work", "personal", "newsletter", "transaction", "social", "spam", "other"

Subject: {subject}

Content:
{content[:4000]}

Respond ONLY with valid JSON, no other text."""

    def _summarize():
      response = self.client.messages.create(
        model=self.model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
      )
      return response.content[0].text

    try:
      result = await loop.run_in_executor(None, _summarize)
      return EmailSummary.from_json(result)
    except Exception as e:
      return EmailSummary(one_liner=f"Summary unavailable: {str(e)[:50]}")

  async def summarize_thread(
    self,
    emails: List[dict],
    max_length: int = 300,
  ) -> str:
    """Summarize an entire email thread.

    Args:
      emails: List of email dicts with 'from', 'date', 'content' keys
      max_length: Maximum summary length in characters

    Returns:
      Thread summary string
    """
    loop = asyncio.get_event_loop()

    thread_text = "\n---\n".join([
      f"From: {e.get('from', 'Unknown')}\nDate: {e.get('date', '')}\n{e.get('content', '')[:500]}"
      for e in emails[-5:]  # Last 5 emails in thread
    ])

    prompt = f"""Summarize this email thread in {max_length} characters or less.
Focus on: current status, pending decisions, and action items.
Be concise and direct.

Thread:
{thread_text}

Summary:"""

    def _summarize():
      response = self.client.messages.create(
        model=self.model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
      )
      return response.content[0].text.strip()

    try:
      return await loop.run_in_executor(None, _summarize)
    except Exception:
      return "Thread summary unavailable"

  async def suggest_replies(
    self,
    subject: str,
    content: str,
    sender: str,
    context: Optional[str] = None,
  ) -> List[ReplyDraft]:
    """Generate smart reply suggestions.

    Args:
      subject: Original email subject
      content: Original email content
      sender: Sender's name/email
      context: Additional context about the user

    Returns:
      List of ReplyDraft suggestions
    """
    loop = asyncio.get_event_loop()

    context_text = f"\nContext about me: {context}" if context else ""

    prompt = f"""Given this email, suggest 3 reply options as JSON array.
Each reply should have: "tone", "subject", "content"
Tones: "formal" (professional), "casual" (friendly), "brief" (quick acknowledgment)

From: {sender}
Subject: {subject}

Content:
{content[:2000]}
{context_text}

Respond ONLY with a JSON array of 3 reply objects. Example format:
[{{"tone": "formal", "subject": "Re: ...", "content": "Dear..."}}]"""

    def _suggest():
      response = self.client.messages.create(
        model=self.model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
      )
      return response.content[0].text

    try:
      result = await loop.run_in_executor(None, _suggest)
      replies_data = json.loads(result)
      return [ReplyDraft.from_dict(r) for r in replies_data]
    except Exception:
      return []

  async def categorize_batch(
    self,
    emails: List[dict],
  ) -> dict[str, EmailCategory]:
    """Categorize multiple emails at once for efficiency.

    Args:
      emails: List of email dicts with 'id', 'subject', 'preview' keys

    Returns:
      Dict mapping email IDs to categories
    """
    loop = asyncio.get_event_loop()

    if not emails:
      return {}

    # Limit batch size
    emails = emails[:20]

    email_list = "\n".join([
      f"ID:{e['id']} SUBJ:{e['subject'][:50]} PREV:{e.get('preview', '')[:100]}"
      for e in emails
    ])

    prompt = f"""Categorize each email into one of: work, personal, newsletter, transaction, social, spam, other

Return JSON object mapping ID to category. Example: {{"email1": "work", "email2": "newsletter"}}

Emails:
{email_list}

JSON response:"""

    def _categorize():
      response = self.client.messages.create(
        model=self.model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
      )
      return response.content[0].text

    try:
      result = await loop.run_in_executor(None, _categorize)
      categories_data = json.loads(result)
      return {
        k: EmailCategory(v) for k, v in categories_data.items()
        if v in [c.value for c in EmailCategory]
      }
    except Exception:
      return {}

  async def compose_draft(
    self,
    to: str,
    purpose: str,
    tone: str = "professional",
    context: Optional[str] = None,
  ) -> dict:
    """Help compose a new email.

    Args:
      to: Recipient description (e.g., "my boss", "client")
      purpose: What the email should accomplish
      tone: Desired tone (professional, casual, formal)
      context: Additional context

    Returns:
      Dict with 'subject' and 'body' keys
    """
    loop = asyncio.get_event_loop()

    context_text = f"\nContext: {context}" if context else ""

    prompt = f"""Write an email with these requirements:
- To: {to}
- Purpose: {purpose}
- Tone: {tone}
{context_text}

Return JSON with "subject" and "body" keys.
Keep it concise and professional unless otherwise specified.

JSON response:"""

    def _compose():
      response = self.client.messages.create(
        model=self.model,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
      )
      return response.content[0].text

    try:
      result = await loop.run_in_executor(None, _compose)
      return json.loads(result)
    except Exception:
      return {"subject": "", "body": ""}
