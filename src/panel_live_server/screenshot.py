"""Headless-browser screenshot capture for rendered Panel snippets.

Wraps Playwright (Chromium) to load a ``/view`` page and capture a PNG so the
MCP ``screenshot`` tool can hand an LLM a picture of the *rendered* output —
the actual layout, fonts, and margins as a user would see them, not just the
source code.

Playwright is a **required** dependency (included in the base install). Import /
launch failures are surfaced as :class:`PlaywrightUnavailableError` with an
install hint so callers can degrade gracefully instead of crashing.

By default the bundled Chromium (installed via ``playwright install chromium``)
is used — this is the most reliable choice across operating systems and headless
container environments (JupyterHub, Codespaces, dev containers) that often have
no system browser. To reuse an already-installed browser and skip the download,
set one of:

- ``PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_CHANNEL`` (e.g. ``chrome``, ``msedge``)
- ``PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_PATH``    (path to a Chromium-family binary)
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class PlaywrightUnavailableError(RuntimeError):
    """Raised when Playwright or its Chromium browser is not installed/launchable."""


_INSTALL_HINT = (
    "Screenshot support requires the Chromium browser binary. Install it with:\n"
    "    playwright install chromium\n"
    "Alternatively, reuse an installed browser by setting "
    "PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_CHANNEL=chrome (or msedge), or "
    "PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_PATH=/path/to/chrome."
)

# Selectors that indicate Panel/Bokeh content has been mounted. Best-effort —
# text/markdown-only pages may match none of these, so a miss is not fatal.
_CONTENT_SELECTOR = "canvas, .bk-Row, .bk-Column, .bk, .markdown, table, img, svg"


def is_available() -> bool:
    """Return ``True`` if the Playwright Python package is importable."""
    try:
        import playwright.async_api  # noqa: F401
    except ImportError:
        return False
    return True


class _BrowserManager:
    """Lazily launches and reuses a single shared headless browser."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._lock = asyncio.Lock()

    def _launch_kwargs(self) -> dict:
        """Build ``chromium.launch`` kwargs, honoring optional browser overrides."""
        import os

        kwargs: dict = {"headless": True}
        if channel := os.getenv("PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_CHANNEL", "").strip():
            kwargs["channel"] = channel
        if executable := os.getenv("PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_PATH", "").strip():
            kwargs["executable_path"] = executable
        return kwargs

    async def _ensure_browser(self):
        """Return a connected browser, launching one on first use."""
        if self._browser is not None and self._browser.is_connected():
            return self._browser

        async with self._lock:
            # Re-check inside the lock — another coroutine may have launched it.
            if self._browser is not None and self._browser.is_connected():
                return self._browser

            try:
                from playwright.async_api import async_playwright
            except ImportError as e:
                raise PlaywrightUnavailableError(_INSTALL_HINT) from e

            self._playwright = await async_playwright().start()
            try:
                self._browser = await self._playwright.chromium.launch(**self._launch_kwargs())
            except Exception as e:
                # Most commonly the chromium binary was never installed, or the
                # requested channel/executable does not exist.
                await self._stop_playwright()
                raise PlaywrightUnavailableError(f"Failed to launch a headless browser: {e}\n{_INSTALL_HINT}") from e

            return self._browser

    async def capture(
        self,
        url: str,
        *,
        width: int,
        height: int,
        full_page: bool,
        settle_ms: int,
        timeout_ms: int,
    ) -> bytes:
        """Load ``url`` in a fresh browser context and return a PNG screenshot."""
        browser = await self._ensure_browser()
        context = await browser.new_context(viewport={"width": width, "height": height})
        try:
            page = await context.new_page()
            # Use "load" rather than "networkidle": Panel's ``server`` method keeps
            # a live Bokeh websocket open, so the network never goes idle.
            await page.goto(url, wait_until="load", timeout=timeout_ms)

            # Best-effort wait for Panel/Bokeh content to mount. A timeout here is
            # fine (e.g. text-only output) — we still capture after the settle delay.
            try:
                await page.wait_for_selector(_CONTENT_SELECTOR, timeout=min(5000, timeout_ms))
            except Exception:
                logger.debug("No known content selector matched for %s; capturing anyway.", url)

            # Bokeh draws asynchronously after mount; give the canvas time to settle.
            await page.wait_for_timeout(settle_ms)

            return await page.screenshot(type="png", full_page=full_page)
        finally:
            await context.close()

    async def _stop_playwright(self) -> None:
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    async def shutdown(self) -> None:
        """Close the shared browser and stop Playwright (best-effort, idempotent)."""
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        await self._stop_playwright()


_manager = _BrowserManager()


async def capture_png(
    url: str,
    *,
    width: int = 1200,
    height: int = 800,
    full_page: bool = False,
    settle_ms: int = 1200,
    timeout_ms: int = 30000,
) -> bytes:
    """Capture a PNG screenshot of ``url`` using a shared headless browser.

    Raises
    ------
    PlaywrightUnavailableError
        If Playwright or a launchable browser is not available.
    """
    return await _manager.capture(
        url,
        width=width,
        height=height,
        full_page=full_page,
        settle_ms=settle_ms,
        timeout_ms=timeout_ms,
    )


async def shutdown_browser() -> None:
    """Close the shared browser (best-effort). Safe to call when never launched."""
    await _manager.shutdown()
