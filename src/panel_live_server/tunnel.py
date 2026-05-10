"""Ngrok HTTPS tunnel for Panel Live Server.

Exposes the local Panel server via a public HTTPS URL so MCP clients that
block ``frame-src localhost`` (e.g. Claude Desktop) can embed the Panel
session in an iframe — giving full Python-backed interactivity (sliders,
callbacks, ``@pn.depends``) without a Pyodide/WASM workaround.

Usage
-----
Set ``PANEL_LIVE_SERVER_NGROK_TOKEN`` in the environment (or in
``claude_desktop_config.json`` under ``env``). The MCP server will
automatically start the tunnel at startup and stop it on shutdown.

Get a free auth token at https://dashboard.ngrok.com/get-started/your-authtoken
"""

import logging
import sys
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def _stdout_to_stderr():
    """Redirect stdout to stderr for the duration of the context.

    pyngrok prints download-progress text via ``print()`` to stdout on first
    use. In MCP stdio transport every byte on stdout is treated as a JSON-RPC
    message, so any plain text corrupts the channel. Redirecting to stderr
    keeps the output visible in logs without breaking the protocol.
    """
    old = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old

_tunnel = None  # active pyngrok tunnel handle


def start_ngrok(port: int, authtoken: str = "") -> str | None:
    """Start an ngrok HTTPS tunnel to *port* and return the public URL.

    Returns ``None`` if pyngrok is not installed or the tunnel fails —
    the server continues without a tunnel in that case.

    Parameters
    ----------
    port : int
        Local port to expose (the Panel server port, default 5077).
    authtoken : str, optional
        Ngrok auth token from https://dashboard.ngrok.com.
        Required for unattended use. If empty, ngrok reuses a previously
        authenticated local agent config (``~/.ngrok2/ngrok.yml``).

    Returns
    -------
    str | None
        Public HTTPS URL such as ``"https://abc123.ngrok.io"`` or ``None``.
    """
    global _tunnel

    try:
        from pyngrok import conf, ngrok
    except ImportError:
        logger.warning(
            "pyngrok not installed — ngrok tunnel disabled. "
            "Install with: pip install pyngrok"
        )
        return None

    try:
        if authtoken:
            conf.get_default().auth_token = authtoken

        with _stdout_to_stderr():
            _tunnel = ngrok.connect(port, "http")
        url: str = _tunnel.public_url

        # pyngrok may return http:// — normalise to https://
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]

        logger.info("Ngrok tunnel active: %s → localhost:%s", url, port)
        return url

    except Exception as exc:
        logger.error("Failed to start ngrok tunnel: %s", exc)
        return None


def stop_ngrok() -> None:
    """Disconnect all ngrok tunnels and kill the local ngrok agent process."""
    global _tunnel
    if _tunnel is None:
        return
    try:
        from pyngrok import ngrok

        ngrok.kill()
        logger.info("Ngrok tunnel stopped")
    except Exception as exc:
        logger.debug("Error stopping ngrok: %s", exc)
    finally:
        _tunnel = None
