def test_init_app_db_creates_tables(tmp_path):
    from givlocal.database import init_app_db

    db_path = str(tmp_path / "app.db")
    conn = init_app_db(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    assert "api_tokens" in tables
    assert "events" in tables
    assert "inverters" in tables
    assert "settings_map" in tables
    assert "preset_profiles" in tables
    conn.close()


def test_init_app_db_is_idempotent(tmp_path):
    from givlocal.database import init_app_db

    db_path = str(tmp_path / "app.db")
    conn1 = init_app_db(db_path)
    conn1.execute("INSERT INTO api_tokens (name, token_hash) VALUES ('test', 'abc')")
    conn1.commit()
    conn1.close()
    conn2 = init_app_db(db_path)
    row = conn2.execute("SELECT name FROM api_tokens WHERE token_hash='abc'").fetchone()
    assert row[0] == "test"
    conn2.close()
