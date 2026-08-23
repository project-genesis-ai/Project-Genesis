from genesis.persistence.store import _chunks, database_url


def test_render_database_url_preserves_hostname(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@dpg-example-a.oregon-postgres.render.com/db")
    value = database_url()
    assert value.startswith("postgresql+psycopg://u:p@dpg-example-a.oregon-postgres.render.com/db")
    assert "sslmode=require" in value


def test_chunks_are_small_and_lossless():
    payload = bytes(range(256)) * 9000
    chunks = list(_chunks(payload))
    assert len(chunks) > 1
    assert all(len(chunk) <= 1024 * 1024 for _, chunk in chunks)
    assert b"".join(chunk for _, chunk in chunks) == payload
    assert [index for index, _ in chunks] == list(range(len(chunks)))
