import hashlib
import secrets
import sqlite3


def generate_token() -> tuple[str, str]:
    """Generate a new token. Returns (plaintext, sha256_hash)."""
    plaintext = secrets.token_hex(32)
    token_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    return plaintext, token_hash


def verify_token(plaintext: str, token_hash: str) -> bool:
    """Return True if sha256(plaintext) matches token_hash."""
    return hashlib.sha256(plaintext.encode()).hexdigest() == token_hash


class TokenStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, name: str, plaintext: str) -> None:
        """Hash plaintext and store a new token record."""
        token_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        self._conn.execute(
            "INSERT INTO api_tokens (name, token_hash) VALUES (?, ?)",
            (name, token_hash),
        )
        self._conn.commit()

    def validate(self, plaintext: str) -> bool:
        """Return True if plaintext matches a stored token, updating last_used_at."""
        token_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        row = self._conn.execute(
            "SELECT id FROM api_tokens WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        if row is None:
            return False
        self._conn.execute(
            "UPDATE api_tokens SET last_used_at = datetime('now') WHERE id = ?",
            (row[0],),
        )
        self._conn.commit()
        return True

    def list_all(self) -> list[dict]:
        """Return all tokens as a list of dicts (without the hash)."""
        cursor = self._conn.execute("SELECT id, name, created_at, last_used_at FROM api_tokens ORDER BY id")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
