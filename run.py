"""
MCP-CanaryTrap - Render and local entry point.

The root URL is redirected to /dashboard so visitors see the web interface
instead of the JSON health/status response.
"""

import os

import uvicorn
from starlette.responses import RedirectResponse


class DashboardRootRedirect:
    """ASGI wrapper that sends GET/HEAD / requests to /dashboard."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") == "/" and scope.get("method") in {"GET", "HEAD"}:
            response = RedirectResponse(url="/dashboard", status_code=307)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def main() -> None:
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8000"))

    print("=" * 65)
    print("MCP-CanaryTrap | Integrated Security & Vulnerability Assessment")
    print("=" * 65)
    print(f"Listening on : {host}:{port}")
    print(f"Website      : /  -> /dashboard")
    print(f"Dashboard    : /dashboard")
    print(f"API docs     : /docs")
    print("=" * 65)

    # Import only after environment configuration is read.
    from app.main import app

    # Keep the FastAPI application unchanged; redirect only the website root.
    web_app = DashboardRootRedirect(app)

    uvicorn.run(
        web_app,
        host=host,
        port=port,
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level="info",
    )


if __name__ == "__main__":
    main()
