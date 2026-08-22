from __future__ import annotations

import os
import pickle

import pytest

from genesis.persistence.store import GenesisStore, _compress, _decompress


def test_checkpoint_compression_round_trip() -> None:
    payload = (b"Genesis authoritative state " * 10000) + os.urandom(256)
    compressed = _compress(payload)
    assert len(compressed) < len(payload)
    assert _decompress(compressed) == payload
    assert _decompress(payload) == payload


def test_compressed_pickle_round_trip() -> None:
    simulation = {"tick": 0, "agents": [], "planet": {"cells": [1, 2, 3]}}
    encoded = _compress(pickle.dumps(simulation, protocol=pickle.HIGHEST_PROTOCOL))
    assert pickle.loads(_decompress(encoded)) == simulation


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is required for PostgreSQL integration")
def test_database_ping() -> None:
    assert GenesisStore().ping() is True
