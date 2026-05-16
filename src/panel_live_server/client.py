"""HTTP client for Display Server REST API.

This module provides a client for interacting with the Panel Display Server
via its REST API. The client can be used with either a locally-managed subprocess
or a remote server instance.
"""

import logging

import requests  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class DisplayClient:
    """HTTP client for Display Server REST API.

    This client handles all HTTP communication with the Panel Display Server,
    including health checks and snippet creation. It uses a persistent session
    for connection pooling.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize the Display Client.

        Parameters
        ----------
        base_url : str
            Base URL of the Display Server (e.g., "http://localhost:5077")
        timeout : int
            Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def is_healthy(self) -> bool:
        """Check if Display Server is healthy.

        Returns
        -------
        bool
            True if server responds to health check, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def create_snippet(self, code: str, name: str = "", description: str = "", method: str = "inline") -> dict:
        """Create a visualization snippet on the Display Server.

        Sends Python code to the server for execution and rendering.

        Parameters
        ----------
        code : str
            Python code to execute
        name : str, optional
            Name for the visualization
        description : str, optional
            Description of the visualization
        method : str, optional
            Execution method ("inline" or "server")

        Returns
        -------
        dict
            Server response containing either:
            - Success: {"url": str, "id": str, ...}
            - Error: {"error": str, "message": str, "traceback": str}

        Raises
        ------
        RuntimeError
            If HTTP request fails
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/snippet",
                json={
                    "code": code,
                    "name": name,
                    "description": description,
                    "method": method,
                },
                timeout=self.timeout,
            )

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.exception(f"Error creating visualization: {e}")
            raise RuntimeError(f"Failed to create visualization: {e}") from e

    def get_embed_html(self, snippet_id: str) -> str | None:
        """Fetch self-contained static HTML for a jupyter-method snippet.

        Returns ``None`` on failure so the caller can degrade gracefully.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/embed",
                params={"id": snippet_id},
                timeout=self.timeout,
            )
            if response.status_code != 200:
                logger.warning("Embed render failed (HTTP %s) for snippet %s", response.status_code, snippet_id)
                return None
            if "text/html" not in response.headers.get("Content-Type", ""):
                logger.warning("Embed render returned non-HTML content-type for snippet %s", snippet_id)
                return None
            return response.text
        except requests.RequestException as e:
            logger.warning("Embed render request error for snippet %s: %s", snippet_id, e)
            return None

    def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
