"""Secure password generator for new logins."""

import secrets
import string
from dataclasses import dataclass
from typing import Optional


@dataclass
class PasswordOptions:
  """Password generation options."""
  length: int = 24
  include_uppercase: bool = True
  include_lowercase: bool = True
  include_digits: bool = True
  include_symbols: bool = True
  exclude_ambiguous: bool = True  # Exclude 0, O, l, 1, etc.


# Characters that are easily confused
AMBIGUOUS_CHARS = "0O1lI|"


def generate_password(options: Optional[PasswordOptions] = None) -> str:
  """Generate a secure random password.

  Args:
    options: Password generation options

  Returns:
    Secure random password string
  """
  if options is None:
    options = PasswordOptions()

  # Build character set
  chars = ""

  if options.include_lowercase:
    chars += string.ascii_lowercase
  if options.include_uppercase:
    chars += string.ascii_uppercase
  if options.include_digits:
    chars += string.digits
  if options.include_symbols:
    chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"

  # Remove ambiguous characters if requested
  if options.exclude_ambiguous:
    chars = "".join(c for c in chars if c not in AMBIGUOUS_CHARS)

  if not chars:
    chars = string.ascii_letters + string.digits

  # Generate password
  password = "".join(secrets.choice(chars) for _ in range(options.length))

  return password


def generate_memorable_password(num_words: int = 4, separator: str = "-") -> str:
  """Generate a memorable password using random words.

  Args:
    num_words: Number of words to include
    separator: Character to separate words

  Returns:
    Memorable password like "correct-horse-battery-staple"
  """
  # Common words for memorable passwords
  words = [
    "apple", "banana", "cherry", "dragon", "eagle", "forest",
    "galaxy", "harbor", "island", "jungle", "koala", "lemon",
    "mango", "nebula", "ocean", "planet", "quartz", "river",
    "sunset", "thunder", "umbrella", "violet", "whisper", "xylophone",
    "yellow", "zenith", "anchor", "bridge", "castle", "diamond",
    "emerald", "falcon", "garden", "hunter", "indigo", "jasper",
    "kiwi", "lantern", "marble", "ninja", "orange", "phoenix",
    "quantum", "rainbow", "silver", "tiger", "ultra", "velvet",
    "willow", "xenon", "yacht", "zephyr", "alpine", "blazer",
    "cosmic", "delta", "echo", "frost", "glider", "horizon",
  ]

  selected = [secrets.choice(words) for _ in range(num_words)]

  # Add a random number at the end for extra security
  selected.append(str(secrets.randbelow(100)))

  return separator.join(selected)


def password_strength(password: str) -> dict:
  """Analyze password strength.

  Args:
    password: Password to analyze

  Returns:
    Dict with strength info
  """
  has_lower = any(c.islower() for c in password)
  has_upper = any(c.isupper() for c in password)
  has_digit = any(c.isdigit() for c in password)
  has_symbol = any(c in string.punctuation for c in password)

  length = len(password)

  # Calculate score
  score = 0
  if length >= 8:
    score += 1
  if length >= 12:
    score += 1
  if length >= 16:
    score += 1
  if length >= 24:
    score += 1

  if has_lower:
    score += 1
  if has_upper:
    score += 1
  if has_digit:
    score += 1
  if has_symbol:
    score += 1

  # Strength rating
  if score >= 7:
    strength = "strong"
    color = "#00FF88"
  elif score >= 5:
    strength = "good"
    color = "#00D4FF"
  elif score >= 3:
    strength = "moderate"
    color = "#FFB800"
  else:
    strength = "weak"
    color = "#FF4444"

  return {
    "score": score,
    "max_score": 8,
    "strength": strength,
    "color": color,
    "length": length,
    "has_lowercase": has_lower,
    "has_uppercase": has_upper,
    "has_digits": has_digit,
    "has_symbols": has_symbol,
  }
