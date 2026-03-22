import os
import sys

try:
    import importlib.metadata as _md
except ImportError:
    import importlib_metadata as _md

import pytest

if sys.platform == "win32":
    from aiohttp.resolver import ThreadedResolver
    import homeassistant.helpers.aiohttp_client as ha_aiohttp_client
    import homeassistant.helpers.backports.aiohttp_resolver as ha_aiohttp_resolver
    import pytest_socket

    class WindowsThreadedResolver(ThreadedResolver):
        """Avoid aiodns/proactor incompatibilities in Windows test runs."""

    ha_aiohttp_resolver.AsyncResolver = WindowsThreadedResolver
    ha_aiohttp_client.AsyncResolver = WindowsThreadedResolver

    if not hasattr(os, "fchmod"):
        def _noop_fchmod(_fd: int, _mode: int) -> None:
            return None

        os.fchmod = _noop_fchmod


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup() -> None:
    """Keep Windows event-loop setup working while still blocking outbound network."""
    if sys.platform != "win32":
        return

    # The Home Assistant pytest plugin disables socket creation globally and only
    # allows Unix sockets for asyncio internals. On Windows, asyncio falls back
    # to loopback TCP sockets for socketpair(), so event-loop creation fails
    # before any test logic runs. Re-enable socket creation and keep connect()
    # restricted to loopback for the rest of the test.
    pytest_socket.enable_socket()
    pytest_socket.socket_allow_hosts(["127.0.0.1", "localhost", "::1"])


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_fixture_setup(fixturedef):
    """Allow Windows asyncio to create its loopback self-pipe during event-loop setup."""
    if sys.platform == "win32" and fixturedef.argname == "event_loop":
        pytest_socket.enable_socket()
        pytest_socket.socket_allow_hosts(["127.0.0.1", "localhost", "::1"])

    yield


if hasattr(_md, "_thread_executor"):
    _md._thread_executor.shutdown(wait=False)
    delattr(_md, "_thread_executor")
