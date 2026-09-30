import socket

import pytest

# Unit tests check the framework itself, offline. Any attempt to open a connection fails the test
# instead of quietly calling DummyJSON.


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise RuntimeError("Unit tests must not use the network")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
