"""Headless-browser screenshot capture for rendered Panel snippets.

Wraps Playwright (Chromium) to load a ``/view`` page and capture a PNG so the
MCP ``screenshot`` tool can hand an LLM a picture of the *rendered* output —
the actual layout, fonts, and margins as a user would see them, not just the
source code.

Playwright is a **required** dependency (included in the base install). Import /
launch failures are surfaced as :class:`PlaywrightUnavailableError` with an
install hint so callers can degrade gracefully instead of crashing.

Browser selection is automatic — no manual install step required:

1. If system **Chrome** or **Edge** is found, it is used immediately (no download).
2. Otherwise the bundled **Chromium** is tried; if absent it is downloaded (~150 MB).
3. If that fails, **Firefox** then **WebKit** are tried (same: use if present, download if not).

To pin a specific browser instead of auto-detecting, set one of:

- ``PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_CHANNEL`` (e.g. ``chrome``, ``msedge``)
- ``PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_PATH``    (path to a Chromium-family binary)
"""

import asyncio
import logging
import os
import sys

logger = logging.getLogger(__name__)


class PlaywrightUnavailableError(RuntimeError):
    """Raised when Playwright or its browser is not installed/launchable."""


_INSTALL_HINT = (
    "Could not find or install any browser. Try installing one manually:\n"
    "    playwright install chromium\n"
    "Or reuse an existing browser by setting:\n"
    "    PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_CHANNEL=chrome  (or msedge)\n"
    "    PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_PATH=/path/to/browser"
)

# System Chrome/Edge can be used via Playwright's channel API — no download needed.
_SYSTEM_CHANNELS = ("chrome", "msedge")

# Playwright-bundled engines tried in order when no system browser is found.
# Each is installed on demand if not already present.
_FALLBACK_ENGINES = ("chromium", "firefox", "webkit")

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
    """Lazily launches and reuses a single shared headless browser.

    Browser selection order (first success wins):

    1. Env-var override (``PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_CHANNEL`` /
       ``..._BROWSER_PATH``) — user picks explicitly, no auto-detection.
    2. System Chrome → system Edge (channel API, zero download).
    3. Bundled Chromium → Firefox → WebKit (each installed on demand if absent).
    """

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._lock = asyncio.Lock()

    def _has_override(self) -> bool:
        """Return True when the user set an explicit browser env var."""
        return bool(
            os.getenv("PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_CHANNEL", "").strip()
            or os.getenv("PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_PATH", "").strip()
        )

    def _override_kwargs(self) -> dict:
        """Build ``chromium.launch`` kwargs from env var overrides."""
        kwargs: dict = {"headless": True}
        if channel := os.getenv("PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_CHANNEL", "").strip():
            kwargs["channel"] = channel
        if executable := os.getenv("PANEL_LIVE_SERVER_SCREENSHOT_BROWSER_PATH", "").strip():
            kwargs["executable_path"] = executable
        return kwargs

    async def _try_system_browser(self, pw):
        """Try system Chrome then Edge via Playwright channel API (no download)."""
        for channel in _SYSTEM_CHANNELS:
            try:
                browser = await pw.chromium.launch(headless=True, channel=channel)
                logger.info("Using system browser: %s", channel)
                return browser
            except Exception:
                continue
        return None

    async def _install_engine(self, engine_name: str) -> bool:
        """Run ``playwright install <engine>`` and return True on success."""
        logger.info("No browser found — downloading %s (one-time). This may take a minute...", engine_name)
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "playwright", "install", engine_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                logger.info("%s installed successfully.", engine_name)
                return True
            logger.warning("playwright install %s failed:\n%s", engine_name, stdout.decode())
        except Exception as exc:
            logger.warning("Could not install %s: %s", engine_name, exc)
        return False

    async def _launch_fallback(self, pw):
        """Try each bundled engine; install it first if the binary is absent."""
        for engine_name in _FALLBACK_ENGINES:
            engine = getattr(pw, engine_name)
            try:
                browser = await engine.launch(headless=True)
                logger.info("Using bundled %s.", engine_name)
                return browser
            except Exception:
                pass
            if await self._install_engine(engine_name):
                try:
                    browser = await engine.launch(headless=True)
                    return browser
                except Exception:
                    pass
        return None

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
                if self._has_override():
                    self._browser = await self._playwright.chromium.launch(**self._override_kwargs())
                else:
                    self._browser = await self._try_system_browser(self._playwright)
                    if self._browser is None:
                        self._browser = await self._launch_fallback(self._playwright)
                    if self._browser is None:
                        raise RuntimeError("No browser could be launched or installed.")
            except Exception as e:
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
    ) -> tuple[bool, list[str]]:
        """Load ``url`` in a headless browser and return visual feedback as text.

        Returns
        -------
        tuple[bool, list[str]]
            ``(content_found, issues)`` — True if Panel content was detected,
            plus a list of any warning strings (empty means all clear).
        """
        browser = await self._ensure_browser()
        context = await browser.new_context(viewport={"width": width, "height": height})
        try:
            page = await context.new_page()
            # Use "load" rather than "networkidle": Panel's ``server`` method keeps
            # a live Bokeh websocket open, so the network never goes idle.
            await page.goto(url, wait_until="load", timeout=timeout_ms)

            content_found = True
            try:
                await page.wait_for_selector(_CONTENT_SELECTOR, timeout=min(5000, timeout_ms))
            except Exception:
                content_found = False
                logger.debug("No known content selector matched for %s.", url)

            # Bokeh draws asynchronously after mount; give the canvas time to settle.
            await page.wait_for_timeout(settle_ms)

            # Check for visible error overlays or exception messages in the DOM.
            issues: list[str] = []
            error_text = await page.evaluate(
                """() => {
                    const el = document.querySelector('.error, .exception, [class*="error"], [class*="traceback"]');
                    return el ? el.innerText.trim().slice(0, 300) : null;
                }"""
            )
            if error_text:
                issues.append(f"Error overlay detected: {error_text}")

            return content_found, issues
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


async def capture_feedback(
    url: str,
    *,
    width: int = 1200,
    height: int = 800,
    full_page: bool = False,
    settle_ms: int = 1200,
    timeout_ms: int = 30000,
) -> tuple[bool, list[str]]:
    """Render ``url`` in a headless browser and return text feedback.

    Returns
    -------
    tuple[bool, list[str]]
        ``(content_found, issues)`` — whether Panel content was detected and
        any warning/error strings found on the page.

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
