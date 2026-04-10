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
    assert store.validate(plaintext) is True
    assert store.validate("bogus") is False
    tokens = store.list_all()
    assert len(tokens) == 1
    assert tokens[0]["name"] == "test-token"
    conn.close()
