"""Static HTML rendering of snippets for inline iframe preview.

Executes a snippet's code server-side, captures the resulting Panel object,
and serializes it to a self-contained HTML string that loads Panel/Bokeh JS
from a CDN. The resulting HTML is delivered through the MCP tool result and
rendered via ``iframe.srcdoc`` in the MCP App, bypassing host CSP rules
that block ``frame-src localhost`` (e.g. Claude Desktop).

Bokeh's JS interactivity (zoom, pan, hover, tooltips, selection, linked
brushing) is preserved in the static export. Widgets that depend on Python
callbacks (sliders that re-run code, ``@pn.depends``) are NOT supported —
there is no Python process backing the page.
"""

import logging
import sys
from io import StringIO

import panel as pn
from bokeh.resources import CDN

from panel_live_server.utils import execute_in_module
from panel_live_server.utils import extract_last_expression
from panel_live_server.utils import find_extensions

logger = logging.getLogger(__name__)


def _collect_servables(code: str) -> list:
    """Execute *code* and return every Panel object that called ``.servable()``.

    Temporarily replaces ``Viewable.servable`` with a capturing stub so we
    end up with the Panel-side objects (not the Bokeh models a real
    ``.servable()`` would push to a Document). The original method is
    restored in a ``finally`` block so other code in the process is not
    affected.
    """
    from panel.viewable import Viewable

    collected: list = []
    original = Viewable.servable

    def capture(self, *_args, **_kwargs):
        collected.append(self)
        return self

    Viewable.servable = capture  # type: ignore[method-assign]
    try:
        execute_in_module(code, module_name="bokeh_app_pls_static_html", cleanup=True)
    finally:
        Viewable.servable = original  # type: ignore[method-assign]

    return collected


def _build_panel_object(code: str, method: str) -> pn.viewable.Viewable:
    """Execute *code* and return a single Panel ``Viewable`` to render."""
    if method == "jupyter":
        try:
            statements, last_expr = extract_last_expression(code)
        except ValueError as e:
            raise ValueError(f"Failed to parse code: {e}") from e

        module_name = "bokeh_app_pls_static_html"
        namespace = execute_in_module(statements, module_name=module_name, cleanup=False)
        try:
            result = eval(last_expr, namespace) if last_expr else None  # noqa: S307
        finally:
            sys.modules.pop(module_name, None)

        if result is None:
            return pn.pane.Markdown("*Code executed successfully (no output to display)*")
        return pn.panel(result, sizing_mode="stretch_width")

    servables = _collect_servables(code)
    if not servables:
        return pn.pane.Markdown("*Code executed successfully (no servable objects found)*")
    if len(servables) == 1:
        return servables[0]
    return pn.Column(*servables)


def convert_to_static_html(code: str, method: str = "jupyter", name: str = "") -> str:
    """Convert a snippet to a self-contained static HTML page.

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
        Self-contained HTML that loads Panel/Bokeh from a CDN and renders
        the visualization without further server interaction.

    Raises
    ------
    ValueError
        If the code cannot be parsed or produces no output.
    Exception
        Any exception raised during code execution is propagated.
    """
    extensions = sorted(find_extensions(code))
    if extensions:
        pn.extension(*extensions)

    panel_obj = _build_panel_object(code, method)
    title = name or "Visualization"

    buf = StringIO()
    panel_obj.save(buf, resources=CDN, title=title)
    return buf.getvalue()
