"""MCP-CanaryTrap integrated web-service entry point for Render and local use."""

import os
import uvicorn


def main() -> None:
    # Render supplies PORT; local execution defaults to 8000.
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8000"))

    print("=" * 65)
    print("MCP-CanaryTrap")
    print("Integrated Security & Vulnerability Assessment Suite")
    print("=" * 65)
    print(f"Listening on {host}:{port}")
    print(f"Dashboard: http://127.0.0.1:{port}/dashboard")
    print(f"API docs : http://127.0.0.1:{port}/docs")
    print("=" * 65)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level="info",
    )


if __name__ == "__main__":
    main()
