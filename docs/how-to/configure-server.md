# Configure Panel Live Server

This guide shows you how to configure Panel Live Server — the Panel web server that executes
Python code snippets and renders interactive visualizations.

## Prerequisites

- Panel Live Server installed — see [Getting Started](../tutorials/getting-started.md)

---

## Default Configuration

Panel Live Server runs on `localhost:5077` with sensible defaults. No configuration file is
required for local use.

| Setting | Default | Description |
|---|---|---|
| Port | `5077` | Panel server port |
| Host | `localhost` | Server host address |
| Database | `~/.panel-live-server/snippets/snippets.db` | SQLite database path |
| Max restarts | `3` | Maximum automatic restarts on failure |

---

## Configure via Environment Variables

All settings are controlled through environment variables:

```bash
export PANEL_LIVE_SERVER_PORT=9999
export PANEL_LIVE_SERVER_HOST=127.0.0.1
export PANEL_LIVE_SERVER_DB_PATH=/data/my-snippets.db
export PANEL_LIVE_SERVER_MAX_RESTARTS=5
```

Then start the server:

```bash
pls serve
# or, for MCP mode:
pls mcp
```

---

## Configure via CLI Flags

Alternatively, pass settings directly to `pls serve`:

```bash
pls serve --port 9999
pls serve --host 0.0.0.0 --port 8080
pls serve --db-path /data/my-snippets.db
```

Run `pls serve --help` for the full list of options.

---

## Running as an MCP Server

To use Panel Live Server with AI assistants, start it in MCP mode:

```bash
# stdio transport (default — for Claude Desktop, Claude Code, etc.)
pls mcp

# HTTP transport
pls mcp --transport http --host 127.0.0.1 --port 8001

# SSE transport
pls mcp --transport sse
```

The Panel server starts automatically in the background. You do not need to run `pls serve`
separately.

=== "VS Code"

    Add to `.vscode/mcp.json`:

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

=== "Claude Desktop"

    Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
    `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

=== "Claude Code"

    ```bash
    claude mcp add panel-live-server -- pls mcp
    ```

=== "claude.ai"

    claude.ai requires HTTP transport. Start with:

    ```bash
    pls mcp --transport http --port 8001
    ```

    Then expose it publicly via Cloudflare tunnel — see the
    [MCP server tutorial](../tutorials/mcp-server.md) for the full setup.

### Example: Custom port via environment variable

```json
{
  "mcpServers": {
    "panel-live-server": {
      "command": "pls",
      "args": ["mcp"],
      "env": {
        "PANEL_LIVE_SERVER_PORT": "9999"
      }
    }
  }
}
```

---

## External URL and Remote Environments

Panel Live Server needs to know its public URL when running behind a proxy or tunnel so that
visualization URLs returned to clients are reachable from the browser.

The following environment variables are detected automatically (in priority order):

| Variable(s) | Environment |
|---|---|
| `PANEL_LIVE_SERVER_EXTERNAL_URL` | Any — explicit port-inclusive override |
| `JUPYTERHUB_HOST` + `JUPYTERHUB_SERVICE_PREFIX` | JupyterHub with [jupyter-server-proxy](https://jupyter-server-proxy.readthedocs.io/) |
| `CODESPACE_NAME` + `GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN` | GitHub Codespaces |

### claude.ai

claude.ai requires a public URL. Expose the Panel server via a tunnel (Cloudflare, ngrok,
localhost.run, etc.) and set the URL before starting the MCP server:

```bash
cloudflared tunnel --url http://localhost:5077   # copy the printed URL
export PANEL_LIVE_SERVER_EXTERNAL_URL=<url-from-above>
pls mcp --transport http --port 8001
```

See the [MCP server tutorial](../tutorials/mcp-server.md) for the full three-terminal setup.

### JupyterHub

`JUPYTERHUB_SERVICE_PREFIX` is set automatically by JupyterHub. However, `JUPYTERHUB_HOST`
is only set automatically in subdomain-based routing mode. In the more common path-based
routing mode, set it manually in your MCP configuration:

```json
{
  "mcpServers": {
    "panel-live-server": {
      "command": "pls",
      "args": ["mcp"],
      "env": {
        "JUPYTERHUB_HOST": "https://your-hub.example.com"
      }
    }
  }
}
```

Or set the full URL explicitly:

```bash
export PANEL_LIVE_SERVER_EXTERNAL_URL="https://your-hub/user/you/proxy/5077"
pls mcp
```

### GitHub Codespaces

URL detection is automatic — no configuration needed.

---

## Custom Database Location

By default the SQLite database is stored at `~/.panel-live-server/snippets/snippets.db`.
To use a different location:

```bash
export PANEL_LIVE_SERVER_DB_PATH=/path/to/your/snippets.db
pls serve
```

Or via CLI:

```bash
pls serve --db-path /path/to/your/snippets.db
```

---

## Configuring Auto-Restart Behaviour

Panel Live Server automatically restarts the Panel subprocess if it becomes unhealthy, up to
`max_restarts` times. Adjust this limit:

```bash
export PANEL_LIVE_SERVER_MAX_RESTARTS=5
pls mcp
```

Set to `0` to disable automatic restarts.

---

## Troubleshooting

### Port Already in Use

Change the port:

```bash
pls serve --port 5078
```

Or find and stop the process using the port:

```bash
# Linux / macOS
lsof -ti:5077 | xargs kill -9

# Windows
netstat -ano | findstr :5077
```

### Server Not Responding

Check server health:

```bash
pls status
```

Or query the health endpoint directly:

```bash
curl http://localhost:5077/api/health
```

A healthy server returns `{"status": "ok", ...}`.

### Visualizations Not Displaying

1. Confirm the server is running: `pls status`
2. Check that `show` is listed when you ask your AI assistant for available MCP tools
3. Restart the MCP server if the Panel subprocess failed to start (check startup logs)

---

## Next Steps

- [Architecture](../explanation/architecture.md) — understand how the components fit together
- [Getting Started Tutorial](../tutorials/getting-started.md) — create your first visualization
- [API Reference](../reference/panel_live_server.md) — full reference documentation
