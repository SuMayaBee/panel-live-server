# Tutorial: Installation

In this tutorial you'll install Panel Live Server so that the `pls` command is available in your
terminal. By the end, `pls --version` will print the installed version.

## What You'll Need

- Python 3.12 or later
- A package manager: [`uv`](https://docs.astral.sh/uv/), `pip` (built into Python), or [`pixi`](https://pixi.sh)

---

## Install Panel Live Server

=== "uv"

    ```bash
    # Install
    uv tool install "panel-live-server[pydata]"

    # Find the pls path
    which pls
    # typically: /home/<user>/.local/bin/pls
    ```

=== "pip"

    ```bash
    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # on Linux/macOS

    # Install
    pip install "panel-live-server[pydata]"

    # Find the pls path
    which pls
    # typically: /path/to/venv/bin/pls
    ```

=== "pixi"

    ```bash
    # Initialize and install
    pixi init
    pixi add python
    pixi add --pypi "panel-live-server[pydata]"

    # Find the pls path
    pixi run which pls
    # typically: /path/to/project/.pixi/envs/default/bin/pls
    ```

The `[pydata]` extra includes the full visualization stack used in these tutorials:

> hvplot · plotly · altair · matplotlib · seaborn · holoviews · polars · duckdb · and more

!!! tip "Only need the core server?"
    Install without extras if you only want to serve your own code and manage packages yourself:
    ```bash
    uv tool install panel-live-server
    pip install panel-live-server
    pixi add --pypi panel-live-server
    ```

---

## Verify the installation

```bash
pls --version
```

You should see the installed version printed. If the command is not found, ensure your uv tools
directory is on your PATH — run `uv tool update-shell` and restart your terminal.

---

## Connect to your MCP client

=== "VS Code"

    Add to `.vscode/mcp.json` (create if it doesn't exist):

    ```json
    {
      "servers": {
        "panel-live-server": {
          "type": "stdio",
          "command": "/path/to/pls",
          "args": ["mcp"]
        }
      }
    }
    ```

    !!! warning "Use your absolute path"
        Replace `"command": "/path/to/pls"` with the path printed by `which pls` above —
        e.g. `"command": "/home/user/.local/bin/pls"`

=== "Cursor"

    Add to `~/.cursor/mcp.json`:

    ```json
    {
      "mcpServers": {
        "panel-live-server": {
          "command": "/path/to/pls",
          "args": ["mcp"]
        }
      }
    }
    ```

    !!! warning "Use your absolute path"
        Replace `"command": "/path/to/pls"` with the path printed by `which pls` above —
        e.g. `"command": "/home/user/.local/bin/pls"`

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
          "command": "/path/to/pls",
          "args": ["mcp"]
        }
      }
    }
    ```

    !!! warning "Use your absolute path"
        Replace `"command": "/path/to/pls"` with the path printed by `which pls` above —
        e.g. `"command": "/home/user/.local/bin/pls"`

    Restart Claude Desktop.

    !!! note "Enable the connector in Cowork"
        To use the `show` tool from Cowork, open **Customize → Connectors →
        panel-live-server** and set its permission to **Always Allow** (runs
        without prompting) or **Needs approval** (asks before each call). If the
        connector is left disabled, the tool won't be available in Cowork.

=== "Claude Code"

    ```bash
    claude mcp add panel-live-server -- /path/to/pls mcp
    ```

    !!! warning "Use your absolute path"
        Replace `/path/to/pls` with the path printed by `which pls` above —
        e.g. `claude mcp add panel-live-server -- /home/user/.local/bin/pls mcp`

=== "claude.ai"

    claude.ai requires HTTP transport and a public URL. You can use any tunneling service
    (ngrok, Cloudflare, localhost.run, etc.) — this example uses Cloudflare.

    **Terminal 1** — start the MCP server:

    ```bash
    /path/to/pls mcp --transport http --port 8001
    ```

    !!! warning "Use your absolute path"
        Replace `/path/to/pls` with the path printed by `which pls` above —
        e.g. `/home/user/.local/bin/pls mcp --transport http --port 8001`

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
    /path/to/pls mcp --transport http --port 8001
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
    /path/to/pls serve
    # Open http://localhost:5077/add in your browser
    ```

---

## Add packages to the server environment

Because Panel Live Server runs in an isolated tool environment, it executes your Python snippets
using the packages installed *in that environment*. To add a package:

=== "uv"

    ```bash
    uv tool install --with my-package "panel-live-server[pydata]"
    ```

    You can chain multiple `--with` flags:

    ```bash
    uv tool install --with prophet --with xgboost "panel-live-server[pydata]"
    ```

    !!! note "Upgrading"
        To upgrade to the latest version:
        ```bash
        uv tool upgrade panel-live-server
        ```

=== "pixi"

    ```bash
    pixi add --pypi my-package
    ```

    For example, to add `prophet`:

    ```bash
    pixi add --pypi prophet
    ```

    !!! note "Upgrading"
        To upgrade to the latest version:
        ```bash
        pixi upgrade panel-live-server
        ```

No server restart is needed — the package is available immediately the next time the server starts.

---

## What You've Learned

- Install Panel Live Server as a uv tool with the `[pydata]` extras
- Verify the installation with `pls --version`
- Add extra packages to the server environment with `--with`

## Next Steps

- **[Use the standalone server](standalone-server.md)** — create, view, and manage visualizations
- **[Use the MCP server](mcp-server.md)** — enable AI assistants to render visualizations in your IDE
