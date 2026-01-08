"""Secure credential management via system keyring."""

from typing import Optional
import keyring

SERVICE_NAME = "fastmail-tui"


class CredentialManager:
  """Secure credential management via system keyring.

  Uses the system keyring (macOS Keychain, Windows Credential Manager,
  or Secret Service on Linux) to securely store sensitive credentials.
  """

  def get_fastmail_token(self) -> Optional[str]:
    """Retrieve Fastmail API token from keyring."""
    try:
      return keyring.get_password(SERVICE_NAME, "fastmail_token")
    except keyring.errors.KeyringError:
      return None

  def set_fastmail_token(self, token: str) -> None:
    """Store Fastmail API token in keyring."""
    keyring.set_password(SERVICE_NAME, "fastmail_token", token)

  def delete_fastmail_token(self) -> None:
    """Remove Fastmail API token from keyring."""
    try:
      keyring.delete_password(SERVICE_NAME, "fastmail_token")
    except keyring.errors.PasswordDeleteError:
      pass

  def get_claude_api_key(self) -> Optional[str]:
    """Retrieve Claude API key from keyring."""
    try:
      return keyring.get_password(SERVICE_NAME, "claude_api_key")
    except keyring.errors.KeyringError:
      return None

  def set_claude_api_key(self, key: str) -> None:
    """Store Claude API key in keyring."""
    keyring.set_password(SERVICE_NAME, "claude_api_key", key)

  def delete_claude_api_key(self) -> None:
    """Remove Claude API key from keyring."""
    try:
      keyring.delete_password(SERVICE_NAME, "claude_api_key")
    except keyring.errors.PasswordDeleteError:
      pass

  def get_cache_key(self) -> Optional[str]:
    """Retrieve cache encryption key from keyring."""
    try:
      return keyring.get_password(SERVICE_NAME, "cache_key")
    except keyring.errors.KeyringError:
      return None

  def set_cache_key(self, key: str) -> None:
    """Store cache encryption key in keyring."""
    keyring.set_password(SERVICE_NAME, "cache_key", key)

  def has_fastmail_credentials(self) -> bool:
    """Check if Fastmail credentials are configured."""
    return self.get_fastmail_token() is not None

  def has_claude_credentials(self) -> bool:
    """Check if Claude API key is configured."""
    return self.get_claude_api_key() is not None

  def delete_all(self) -> None:
    """Remove all stored credentials."""
    self.delete_fastmail_token()
    self.delete_claude_api_key()
    try:
      keyring.delete_password(SERVICE_NAME, "cache_key")
    except keyring.errors.PasswordDeleteError:
      pass
