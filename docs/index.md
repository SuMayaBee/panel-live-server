# panel-live-server

[![CI](https://img.shields.io/github/actions/workflow/status/panel-extensions/panel-live-server/ci.yml?style=flat-square&branch=main)](https://github.com/panel-extensions/panel-live-server/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/panel-live-server?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/panel-live-server)
[![pypi](https://img.shields.io/pypi/v/panel-live-server.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/panel-live-server)
[![python](https://img.shields.io/pypi/pyversions/panel-live-server?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/panel-live-server)

**A local Panel web server that executes Python code snippets and renders the resulting
visualizations as live, interactive web pages** — so humans and AI assistants can display
and inspect Python outputs in real time.

---

## `pls mcp` — AI assistant integration

Give Claude, GitHub Copilot, or any MCP-compatible AI assistant the ability to render
visualizations directly in your IDE. The `validate` and `show` tools execute Python and
return a live URL — no manual setup required.

<video controls autoplay muted loop style="width: 100%; max-width: 100%;">
  <source src="assets/videos/panel-live-server-showcase-mcp.mp4" type="video/mp4">
</video>

```bash
uv tool install panel-live-server[pydata]
pls mcp # configure this command in Claude, Copilot etc.
```

Ask your AI assistant:

> Please show a quick and beautiful Matplotlib trading dashboard

> Please show a basic, interactive Panel app with a slider.

> Now replace the text with a hvplot and show it.

> Please show the most beautiful matplotlib plot

The AI calls `show` to render it — the visualization appears immediately in your chat interface.

---

## `pls serve` — Standalone visualization server

Start a local web server and create interactive visualizations through a browser UI or REST API.
Every snippet gets its own permanent URL.

<video controls autoplay muted loop style="width: 100%; max-width: 100%;">
  <source src="assets/videos/panel-live-server-showcase.mp4" type="video/mp4">
</video>

```bash
uv tool install panel-live-server[pydata]
pls serve # run this command in the terminal
```

Open [http://localhost:5077/add](http://localhost:5077/add) and submit any Python visualization:

```python
import pandas as pd
import hvplot.pandas

df = pd.DataFrame({'Product': ['A', 'B', 'C', 'D'], 'Sales': [120, 95, 180, 150]})
df.hvplot.bar(x='Product', y='Sales', title='Sales by Product')
```

Browse your visualizations at [/feed](http://localhost:5077/feed), manage them at
[/admin](http://localhost:5077/admin), and link directly to any individual chart at `/view?id=...`.

---

## Features

### Two execution methods

- **Inline** (default) — the last expression is automatically displayed, just like a notebook cell
- **Server** — explicit `.servable()` calls for multi-component dashboards with reactive widgets

### Works with any Python visualization library

hvplot · plotly · altair · matplotlib · seaborn · holoviews · bokeh · vega · deckgl · and more

### Persistent storage

Every snippet is saved to a local SQLite database with full-text search. Visualizations survive
server restarts and are accessible by URL at any time.

### Robust subprocess management

The Panel server runs as a managed subprocess with health monitoring and automatic restart
(up to a configurable limit). Port conflicts and stale processes are handled automatically.

### Validate before you render

A dedicated `validate` tool runs four static checks — syntax, security, package
availability, and Panel extension declarations — and returns a structured result before any
rendering happens. `show` reuses the cached result automatically, so there is no
double-validation overhead.

### MCP App UI

When used with a compatible AI client, visualizations render inline with zoom controls
(25 / 50 / 75 / 100 %), one-click URL and code copying, and a loading indicator.

### REST API

```python
import requests

response = requests.post(
    "http://localhost:5077/api/snippet",
    json={"code": "1 + 1", "name": "Addition", "method": "inline"}
)
print(response.json()["url"])
```

### Works everywhere

Local, Jupyter, JupyterHub, VS Code Dev Containers, GitHub Codespaces — URLs are
automatically externalized via Jupyter Server Proxy when needed.

---

## Installation

=== "uv"

    ```bash
    uv tool install "panel-live-server[pydata]"
    ```

=== "pip"

    ```bash
    pip install "panel-live-server[pydata]"
    ```

=== "pixi"

    ```bash
    pixi add panel-live-server
    ```

The `[pydata]` extra includes the full visualization stack (hvplot, plotly, altair, polars, etc.).

!!! warning "Pin your version"

    This project is in its early stages. Pin to a specific version to avoid unexpected changes:

    ```bash
    uv tool install "panel-live-server[pydata]==0.1.0a1"
    pip install "panel-live-server[pydata]==0.1.0a1"
    ```

---

## Quick start

**With an AI assistant** — configure once, then ask your AI to create visualizations with natural language.

=== "VS Code"

    Add to `.vscode/mcp.json` (create if it doesn't exist):

    ```json
    {
      "servers": {
        "panel-live-server": {
          "type": "stdio",
          "command": "pls",
          "args": ["mcp"]
        }
      }
    }
    ```

=== "Cursor"

    Add to `~/.cursor/mcp.json`:

    ```json
    {
      "mcpServers": {
        "panel-live-server": {
          "command": "pls",
          "args": ["mcp"]
        }
      }
    }
    ```

    Open Cursor Settings → MCP and verify the green dot. Use Agent mode in chat.

=== "Claude Desktop"

    Edit the config file for your OS:

    - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
    - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
    - **Linux:** `~/.config/Claude/claude_desktop_config.json`

    ```json
    {
      "mcpServers": {
        "panel-live-server": {
          "command": "pls",
          "args": ["mcp"]
        }
      }
    }
    ```

    Restart Claude Desktop.

=== "Claude Code"

    ```bash
    claude mcp add panel-live-server -- pls mcp
    ```

    The AI will automatically call `validate` first, then `show` — errors are caught before
    rendering so you always get clear, actionable feedback instead of a blank panel.

=== "claude.ai"

    claude.ai requires HTTP transport and a public URL. You can use any tunneling service
    (ngrok, Cloudflare, localhost.run, etc.) — this example uses Cloudflare.

    **Terminal 1** — start the MCP server:

    ```bash
    pls mcp --transport http --port 8001
    ```

    **Terminal 2** — tunnel for the MCP server:

    ```bash
    cloudflared tunnel --url http://localhost:8001
    ```

    **Terminal 3** — tunnel for the Panel server:

    ```bash
    cloudflared tunnel --url http://localhost:5077
    ```

    Stop Terminal 1, set the Panel tunnel URL, and restart:

    ```bash
    export PANEL_LIVE_SERVER_EXTERNAL_URL=<url-from-terminal-3>
    pls mcp --transport http --port 8001
    ```

    Then go to claude.ai → Settings → Connectors → Add custom connector and enter
    `<url-from-terminal-2>/mcp` as the URL.

Once connected, ask your AI: *"Show me a scatter plot of this data using the show tool."*

---

**Without an AI assistant** — use the REST API or the browser UI directly.

=== "REST API"

    ```python
    import requests

    r = requests.post(
        "http://localhost:5077/api/snippet",
        json={
            "code": "import panel as pn\npn.widgets.IntSlider(name='x', start=0, end=100)",
            "name": "Slider",
            "method": "inline",
        }
    )
    print(r.json()["url"])  # http://localhost:5077/view?id=...
    ```

=== "Standalone"

    ```bash
    pls serve
    # Open http://localhost:5077/add in your browser
    ```

---

## Learn more

| | |
| --- | --- |
| [**Tutorial**](tutorials/getting-started.md) | Step-by-step guide: standalone server, AI assistant, REST API |
| [**How-to: Configure**](how-to/configure-server.md) | Custom ports, database path, MCP transport, Jupyter proxy |
| [**Explanation**](explanation/architecture.md) | Architecture, execution methods, design principles |
| [**Reference**](reference/panel_live_server.md) | Full API reference |
| [**Examples**](examples.md) | Copy-paste code snippets |
