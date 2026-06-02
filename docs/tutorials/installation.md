# Tutorial: Installation

In this tutorial you'll install Panel Live Server so that the `pls` command is available in your
terminal. By the end, `pls --version` will print the installed version.

## What You'll Need

- Python 3.12 or later
- [`uv`](https://docs.astral.sh/uv/) installed (`pip install uv` or see the uv docs)

---

## Install Panel Live Server

Install Panel Live Server as a standalone tool using `uv tool install`. This puts the `pls`
command on your PATH in an isolated environment, so it doesn't interfere with your project
dependencies:

```bash
uv tool install "panel-live-server[pydata]"
```

The `[pydata]` extra includes the full visualization stack used in these tutorials:

> hvplot · plotly · altair · matplotlib · seaborn · holoviews · polars · duckdb · and more

!!! tip "Only need the core server?"
    Install without extras if you only want to serve your own code and manage packages yourself:
    ```bash
    uv tool install panel-live-server
    ```

---

## Verify the installation

```bash
pls --version
```

You should see the installed version printed. If the command is not found, ensure your uv tools
directory is on your PATH — run `uv tool update-shell` and restart your terminal.

---

## Add packages to the server environment

Because Panel Live Server runs in an isolated tool environment, it executes your Python snippets
using the packages installed *in that environment*. To add a package:

```bash
uv tool install --with my-package "panel-live-server[pydata]"
```

For example, to add `prophet` for time series forecasting:

```bash
uv tool install --with prophet "panel-live-server[pydata]"
```

You can chain multiple `--with` flags:

```bash
uv tool install --with prophet --with xgboost "panel-live-server[pydata]"
```

No server restart is needed — the package is available immediately the next time the server starts.

!!! note "Upgrading"
    To upgrade to the latest version:
    ```bash
    uv tool upgrade panel-live-server
    ```

---

---

## Development install (local repo)

Clone the repository and install in editable mode so changes to the source take effect immediately.

=== "pixi"

    ```bash
    git clone https://github.com/panel-extensions/panel-live-server.git
    cd panel-live-server
    pixi install
    pixi run postinstall
    pixi run pls --version
    ```

=== "uv"

    ```bash
    git clone https://github.com/panel-extensions/panel-live-server.git
    cd panel-live-server
    uv venv && source .venv/bin/activate
    uv pip install -e ".[dev]"
    pls --version
    ```

!!! note
    Activate your venv (`source .venv/bin/activate`) in every new terminal, or prefix
    commands with `pixi run` if using pixi.

---

## What You've Learned

- Install Panel Live Server as a uv tool with the `[pydata]` extras
- Verify the installation with `pls --version`
- Add extra packages to the server environment with `--with`

## Next Steps

- **[Use the standalone server](standalone-server.md)** — create, view, and manage visualizations
- **[Use the MCP server](mcp-server.md)** — enable AI assistants to render visualizations in your IDE
