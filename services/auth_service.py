"""Authentication service providing secure user registration, password hashing, and session verification."""

import os
import re
import uuid
import sqlite3
import hashlib
import hmac
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, Tuple, Dict, Any


@dataclass
class User:
    """Represents an authenticated user account."""
    id: str
    username: str
    display_name: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)


class AuthService:
    """Manages SQLite-backed user credentials and authentication."""

    def __init__(self, db_path: str = "data/clarifile.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return an SQLite database connection."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize the users table schema."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    @staticmethod
    def _hash_password(password: str, salt: bytes) -> str:
        """Generate a secure PBKDF2-HMAC-SHA256 password hash."""
        derived = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=100000,
        )
        return derived.hex()

    @staticmethod
    def sanitize_username(username: str) -> str:
        """Clean and normalize a username string."""
        return username.strip().lower()

    @staticmethod
    def sanitize_collection_name(username: str) -> str:
        """Generate a valid, isolated ChromaDB collection name for the user."""
        cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", username.strip().lower())
        name = f"user_{cleaned}_kb"[:60]
        # Ensure starts and ends with alphanumeric
        name = re.sub(r"^[^a-zA-Z0-9]+", "u_", name)
        name = re.sub(r"[^a-zA-Z0-9]+$", "_kb", name)
        if len(name) < 3:
            name = f"user_{name}_kb"
        return name[:63]

    def register(
        self,
        username: str,
        password: str,
        display_name: Optional[str] = None,
    ) -> Tuple[bool, Optional[User], str]:
        """Register a new user account.

        Args:
            username: Unique username (at least 3 characters).
            password: User password (at least 6 characters).
            display_name: Optional readable display name.

        Returns:
            Tuple of (success, User object if successful, message).
        """
        clean_user = self.sanitize_username(username)
        if len(clean_user) < 3:
            return False, None, "Username must be at least 3 characters long."

        if not re.match(r"^[a-zA-Z0-9_.-]+$", clean_user):
            return False, None, "Username can only contain letters, numbers, dots, and underscores."

        if len(password) < 6:
            return False, None, "Password must be at least 6 characters long."

        disp_name = (display_name or clean_user).strip()
        if not disp_name:
            disp_name = clean_user

        # Generate unique salt and hash
        salt = os.urandom(32)
        pwd_hash = self._hash_password(password, salt)
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users (id, username, password_hash, salt, display_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (user_id, clean_user, pwd_hash, salt.hex(), disp_name, now_iso),
                )
                conn.commit()

            user = User(
                id=user_id,
                username=clean_user,
                display_name=disp_name,
                created_at=now_iso,
            )
            return True, user, "Account created successfully."

        except sqlite3.IntegrityError:
            return False, None, f"Username '{clean_user}' is already registered."
        except Exception as e:
            return False, None, f"Failed to register account: {str(e)}"

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> Tuple[bool, Optional[User], str]:
        """Authenticate user credentials.

        Args:
            username: Username.
            password: Password.

        Returns:
            Tuple of (success, User object if authenticated, message).
        """
        clean_user = self.sanitize_username(username)
        if not clean_user or not password:
            return False, None, "Please provide both username and password."

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, username, password_hash, salt, display_name, created_at
                FROM users WHERE username = ?;
                """,
                (clean_user,),
            )
            row = cursor.fetchone()

        if not row:
            return False, None, "Invalid username or password."

        stored_hash = row["password_hash"]
        salt_bytes = bytes.fromhex(row["salt"])
        computed_hash = self._hash_password(password, salt_bytes)

        if hmac.compare_digest(stored_hash, computed_hash):
            user = User(
                id=row["id"],
                username=row["username"],
                display_name=row["display_name"],
                created_at=row["created_at"],
            )
            return True, user, "Authentication successful."
        else:
            return False, None, "Invalid username or password."

    def get_user_count(self) -> int:
        """Return the total number of registered users."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) AS cnt FROM users;")
            row = cursor.fetchone()
            return int(row["cnt"]) if row else 0

    def seed_default_user_if_empty(
        self,
        default_username: str = "midhun",
        default_password: str = "password123",
        display_name: str = "Midhun",
    ) -> Optional[User]:
        """Create a default account if the user database is currently empty."""
        if self.get_user_count() == 0:
            success, user, _ = self.register(
                username=default_username,
                password=default_password,
                display_name=display_name,
            )
            if success:
                return user
        return None
