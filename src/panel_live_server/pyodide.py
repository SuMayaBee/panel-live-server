"""Pyodide-based browser rendering of snippets.

Converts a snippet's code into a self-contained HTML page that runs the
visualization in the browser via Pyodide. The resulting HTML is delivered
through the MCP tool result and rendered via ``iframe.srcdoc`` in the MCP
App, bypassing host CSP rules that block ``frame-src localhost`` (e.g.
Claude Desktop).

Uses the ``panel convert`` CLI via subprocess rather than calling
``panel.io.convert.convert_apps`` directly. The Python API uses a
``ProcessPoolExecutor`` internally which hangs when called from within an
already-running subprocess (the MCP server), so the CLI path is safer.
"""

import logging
import subprocess
import sys
import tempfile
from pathlib import Path

from panel_live_server.utils import extract_last_expression
from panel_live_server.utils import find_extensions

logger = logging.getLogger(__name__)

_CONVERT_TIMEOUT = 60  # seconds


def _wrap_for_pyodide(code: str, method: str) -> str:
    """Prepare snippet code so it produces a servable Panel object in Pyodide.

    ``jupyter`` snippets express their result as a trailing expression; in the
    standard server flow the view page wraps that expression in
    ``pn.panel(...).servable()``. In Pyodide there is no view page, so we
    perform the same wrapping inline.

    ``panel`` snippets already call ``.servable()`` and only need their
    required ``pn.extension(...)`` declarations to be present (they should be).

    For ``jupyter`` snippets we also auto-inject ``pn.extension(...)`` calls
    for any extensions inferred from the code (matching what
    ``view_page.create_view`` does at session level).
    """
    if method == "panel":
        return code

    extensions = sorted(find_extensions(code))
    ext_args = ", ".join(f"'{e}'" for e in extensions)
    ext_call = f"pn.extension({ext_args})\n" if extensions else ""

    statements, last_expr = extract_last_expression(code)
    if not last_expr:
        return f"import panel as pn\n{ext_call}{code}\n"

    return (
        f"import panel as pn\n"
        f"{ext_call}"
        f"{statements}\n"
        f"pn.panel({last_expr}).servable()\n"
    )


def convert_to_pyodide_html(code: str, method: str = "jupyter", name: str = "") -> str:
    """Convert a snippet to a self-contained Pyodide HTML page.

    Parameters
    ----------
    code : str
        Python code from the snippet.
    method : {"jupyter", "panel"}
        Execution method — same semantics as the ``show`` tool.
    name : str, optional
        Title for the generated page.

    Returns
    -------
    str
        Self-contained HTML that loads Pyodide + Panel from CDNs and runs
        the snippet client-side in the browser.

    Raises
    ------
    RuntimeError
        If ``panel convert`` exits with a non-zero code or does not produce
        the expected output file.
    subprocess.TimeoutExpired
        If the conversion takes longer than ``_CONVERT_TIMEOUT`` seconds.
    """
    wrapped = _wrap_for_pyodide(code, method)
    title = name or "Visualization"

    with tempfile.TemporaryDirectory(prefix="pls-pyodide-") as tmpdir:
        tmp_path = Path(tmpdir)
        script = tmp_path / "app.py"
        script.write_text(wrapped, encoding="utf-8")

        cmd = [
            sys.executable, "-m", "panel", "convert",
            str(script),
            "--to", "pyodide",
            "--out", str(tmp_path),
            "--title", title,
            "--skip-embed",  # don't prerender server-side; browser executes code
        ]

        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=_CONVERT_TIMEOUT,
        )

        html_path = tmp_path / "app.html"
        if not html_path.exists():
            raise RuntimeError(
                f"panel convert did not produce app.html.\n"
                f"exit code: {result.returncode}\n"
                f"stderr: {result.stderr.strip()}"
            )

        return html_path.read_text(encoding="utf-8")
