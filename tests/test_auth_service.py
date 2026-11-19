"""Unit tests for the user authentication service."""

import os
import pytest
from services.auth_service import AuthService, User


@pytest.fixture
def temp_auth_service(tmp_path):
    """Fixture to create an AuthService using an isolated SQLite database."""
    db_file = str(tmp_path / "test_auth.db")
    return AuthService(db_path=db_file)


def test_register_and_authenticate_success(temp_auth_service):
    """Test successful user registration and subsequent authentication."""
    success, user, msg = temp_auth_service.register(
        username="john_doe",
        password="secretpassword123",
        display_name="John Doe",
    )
    assert success is True
    assert user is not None
    assert user.username == "john_doe"
    assert user.display_name == "John Doe"

    # Authenticate with correct credentials
    auth_ok, auth_user, _ = temp_auth_service.authenticate("john_doe", "secretpassword123")
    assert auth_ok is True
    assert auth_user.id == user.id

    # Authenticate case-insensitive username
    auth_ok2, auth_user2, _ = temp_auth_service.authenticate("JOHN_DOE", "secretpassword123")
    assert auth_ok2 is True
    assert auth_user2.id == user.id


def test_authenticate_invalid_password(temp_auth_service):
    """Test authentication failure with incorrect password."""
    temp_auth_service.register("alice", "mypassword1", "Alice")
    auth_ok, user, msg = temp_auth_service.authenticate("alice", "wrongpassword")
    assert auth_ok is False
    assert user is None
    assert "Invalid username or password" in msg


def test_authenticate_nonexistent_user(temp_auth_service):
    """Test authentication failure for non-existent user."""
    auth_ok, user, msg = temp_auth_service.authenticate("nobody", "somepassword")
    assert auth_ok is False
    assert user is None


def test_register_duplicate_username(temp_auth_service):
    """Test that duplicate usernames are rejected."""
    success1, _, _ = temp_auth_service.register("unique_user", "password123")
    assert success1 is True

    success2, user2, msg2 = temp_auth_service.register("unique_user", "otherpassword")
    assert success2 is False
    assert user2 is None
    assert "already registered" in msg2


def test_register_validation(temp_auth_service):
    """Test registration validation rules (username length, password length)."""
    # Username too short
    ok, _, msg = temp_auth_service.register("ab", "password123")
    assert ok is False
    assert "at least 3 characters" in msg

    # Password too short
    ok, _, msg = temp_auth_service.register("valid_user", "12345")
    assert ok is False
    assert "at least 6 characters" in msg


def test_seed_default_user_if_empty(temp_auth_service):
    """Test automatic seeding of initial user."""
    assert temp_auth_service.get_user_count() == 0
    seeded = temp_auth_service.seed_default_user_if_empty()
    assert seeded is not None
    assert seeded.username == "midhun"
    assert temp_auth_service.get_user_count() == 1

    # Second call should not duplicate
    seeded_again = temp_auth_service.seed_default_user_if_empty()
    assert seeded_again is None
    assert temp_auth_service.get_user_count() == 1


def test_sanitize_collection_name():
    """Verify ChromaDB collection name sanitization."""
    assert AuthService.sanitize_collection_name("midhun") == "user_midhun_kb"
    assert AuthService.sanitize_collection_name("User.Name@123") == "user_user_name_123_kb"
    res = AuthService.sanitize_collection_name("a" * 100)
    assert len(res) <= 63
