def test_generate_token_returns_plaintext_and_hash():
    from givlocal.auth import generate_token

    plaintext, token_hash = generate_token()
    assert len(plaintext) == 64  # 32 bytes hex
    assert token_hash != plaintext
    assert len(token_hash) == 64  # sha256 hex


def test_verify_token_matches():
    from givlocal.auth import generate_token, verify_token

    plaintext, token_hash = generate_token()
    assert verify_token(plaintext, token_hash) is True
    assert verify_token("wrong", token_hash) is False


def test_token_store_crud(tmp_path):
    from givlocal.auth import TokenStore, generate_token
    from givlocal.database import init_app_db

    conn = init_app_db(str(tmp_path / "app.db"))
    store = TokenStore(conn)
    plaintext, _ = generate_token()
    store.create("test-token", plaintext)
    # validate returns the token's scope on success, None on failure
    assert store.validate(plaintext) == "admin"
    assert store.validate("bogus") is None
    tokens = store.list_all()
    assert len(tokens) == 1
    assert tokens[0]["name"] == "test-token"
    assert tokens[0]["scope"] == "admin"

    # scoped token
    read_plain, _ = generate_token()
    store.create("read-only", read_plain, scope="read")
    assert store.validate(read_plain) == "read"
    conn.close()


def test_require_scope_rejects_insufficient(tmp_path):
    """A read-scope token must be refused on a write-scope endpoint."""
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    from givlocal.api.dependencies import require_scope
    from givlocal.auth import TokenStore, generate_token
    from givlocal.database import init_app_db
    from givlocal.state import app_state

    conn = init_app_db(str(tmp_path / "app.db"))
    app_state.app_db = conn
    app_state.token_store = TokenStore(conn)
    app_state.auth_required = True

    read_token, _ = generate_token()
    app_state.token_store.create("r", read_token, scope="read")
    write_token, _ = generate_token()
    app_state.token_store.create("w", write_token, scope="write")

    app = FastAPI()

    @app.post("/write", dependencies=[Depends(require_scope("write"))])
    def _w():
        return {"ok": True}

    client = TestClient(app)
    r = client.post("/write", headers={"Authorization": f"Bearer {read_token}"})
    assert r.status_code == 403
    r = client.post("/write", headers={"Authorization": f"Bearer {write_token}"})
    assert r.status_code == 200
    conn.close()
