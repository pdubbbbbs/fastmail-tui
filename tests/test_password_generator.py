"""Tests for password generator."""

import pytest
from fastmail_tui.services.password_generator import (
  generate_password,
  generate_memorable_password,
  password_strength,
  PasswordOptions,
)


def test_generate_password_default():
  """Test default password generation."""
  password = generate_password()
  assert len(password) == 24
  assert password  # Not empty


def test_generate_password_custom_length():
  """Test custom length password."""
  password = generate_password(PasswordOptions(length=32))
  assert len(password) == 32


def test_generate_password_no_symbols():
  """Test password without symbols."""
  password = generate_password(PasswordOptions(
    length=20,
    include_symbols=False,
  ))
  assert len(password) == 20
  assert not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)


def test_generate_memorable_password():
  """Test memorable password generation."""
  password = generate_memorable_password(num_words=4)
  parts = password.split("-")
  assert len(parts) == 5  # 4 words + number


def test_password_strength_weak():
  """Test weak password strength."""
  strength = password_strength("abc")
  assert strength["strength"] == "weak"
  assert strength["score"] < 3


def test_password_strength_strong():
  """Test strong password strength."""
  password = generate_password(PasswordOptions(length=24))
  strength = password_strength(password)
  assert strength["strength"] in ["strong", "good"]
  assert strength["score"] >= 5
