import hashlib
import hmac
import secrets
import sqlite3


def generate_token() -> tuple[str, str]:
    """Generate a new token. Returns (plaintext, sha256_hash)."""
    plaintext = secrets.token_hex(32)
    token_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    return plaintext, token_hash


def verify_token(plaintext: str, token_hash: str) -> bool:
    """Return True if sha256(plaintext) matches token_hash (constant-time)."""
    candidate = hashlib.sha256(plaintext.encode()).hexdigest()
    return hmac.compare_digest(candidate, token_hash)


class TokenStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, name: str, plaintext: str, scope: str = "admin") -> None:
        """Hash plaintext and store a new token record with the given scope."""
        if scope not in ("read", "write", "admin"):
            raise ValueError(f"scope must be read|write|admin, got {scope!r}")
        token_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        self._conn.execute(
            "INSERT INTO api_tokens (name, token_hash, scope) VALUES (?, ?, ?)",
            (name, token_hash, scope),
        )
        self._conn.commit()

    def validate(self, plaintext: str) -> str | None:
        """Return the token's scope if plaintext matches a stored token, else None.

        Uses constant-time comparison against every stored hash to avoid
        leaking hash-prefix information via timing of DB equality lookups.
        Also refreshes last_used_at on success.
        """
        candidate = hashlib.sha256(plaintext.encode()).hexdigest()
        rows = self._conn.execute("SELECT id, token_hash, scope FROM api_tokens").fetchall()
        matched_id: int | None = None
        matched_scope: str | None = None
        for row_id, token_hash, scope in rows:
            if hmac.compare_digest(candidate, token_hash):
                matched_id = row_id
                matched_scope = scope
        if matched_id is None:
            return None
        self._conn.execute(
            "UPDATE api_tokens SET last_used_at = datetime('now') WHERE id = ?",
            (matched_id,),
        )
        self._conn.commit()
        return matched_scope

    def list_all(self) -> list[dict]:
        """Return all tokens as a list of dicts (without the hash)."""
        cursor = self._conn.execute("SELECT id, name, scope, created_at, last_used_at FROM api_tokens ORDER BY id")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
