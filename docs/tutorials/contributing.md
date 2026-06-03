# Contributing

Contributions are welcome! This guide walks you through forking the repository, setting up a
local development environment, and connecting your local build to an MCP client.

---

## Step 1: Fork and clone

1. [Fork the repository](https://github.com/panel-extensions/panel-live-server/fork) on GitHub.
2. Clone your fork:

```bash
git clone https://github.com/<your-username>/panel-live-server.git
cd panel-live-server
```

3. Create a feature branch:

```bash
git checkout -b feature/YourFeature
```

---

## Step 2: Install

=== "uv"

    ```bash
    uv venv && source .venv/bin/activate
    uv pip install -e ".[dev]"

    # Find the pls path
    which pls
    # typically: /path/to/panel-live-server/.venv/bin/pls
    ```

    !!! note
        Run `source .venv/bin/activate` in every new terminal to re-activate the venv.

=== "pixi"

    ```bash
    pixi install
    pixi run postinstall

    # Find the pls path
    pixi run which pls
    # typically: /path/to/panel-live-server/.pixi/envs/default/bin/pls
    ```

    !!! note
        Prefix commands with `pixi run` (e.g. `pixi run pytest`) to use the pixi env without activating it.

---

## Step 3: Install pre-commit hooks

=== "uv"

    ```bash
    pre-commit install
    ```

=== "pixi"

    ```bash
    pixi run lint-install
    ```

---

## Step 4: Connect to your MCP client

Use the absolute path from `which pls` (uv) or `pixi run which pls` (pixi) above.

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
        Replace `"command": "/path/to/pls"` with the path printed above —
        e.g. `"command": "/path/to/panel-live-server/.venv/bin/pls"`

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
        Replace `"command": "/path/to/pls"` with the path printed above —
        e.g. `"command": "/path/to/panel-live-server/.venv/bin/pls"`

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
        Replace `"command": "/path/to/pls"` with the path printed above —
        e.g. `"command": "/path/to/panel-live-server/.venv/bin/pls"`

    Restart Claude Desktop.

=== "Claude Code"

    ```bash
    claude mcp add panel-live-server -- /path/to/pls mcp
    ```

    !!! warning "Use your absolute path"
        Replace `/path/to/pls` with the path printed above —
        e.g. `claude mcp add panel-live-server -- /path/to/panel-live-server/.venv/bin/pls mcp`

=== "claude.ai"

    claude.ai requires HTTP transport and a public URL. You can use any tunneling service
    (ngrok, Cloudflare, localhost.run, etc.) — this example uses Cloudflare.

    **Terminal 1** — start the MCP server:

    ```bash
    /path/to/pls mcp --transport http --port 8001
    ```

    !!! warning "Use your absolute path"
        Replace `/path/to/pls` with the path printed above —
        e.g. `/path/to/panel-live-server/.venv/bin/pls mcp --transport http --port 8001`

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

---

## Step 5: Make changes and run tests

=== "uv"

    ```bash
    pytest tests/                        # run all tests
    pytest tests/test_validation.py      # run a single file
    pre-commit run --all-files           # lint
    ```

=== "pixi"

    ```bash
    pixi run test                        # run all tests
    pixi run test-coverage               # tests + coverage report
    pixi run lint                        # lint (pre-commit on all files)
    ```

---

## Step 6: Submit a pull request

1. Commit your changes:

```bash
git commit -m 'Add some feature'
```

2. Push to your fork:

```bash
git push origin feature/YourFeature
```

3. Open a pull request against the `main` branch on GitHub.

Please ensure your code passes all tests and linting before submitting.
