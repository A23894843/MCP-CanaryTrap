# How to read the annotated MCP-CanaryTrap source

This archive keeps the original project layout and adds explanatory comments directly to the source files.

## What the comments mean
- Python files: comments beginning `# Explanation:` describe the statement, branch, function, class, import, return, or error-handling operation immediately below them.
- `src/mcp_canarytrap/templates/index.html`: HTML comments explain the main UI sections; CSS comments explain styling rules; JavaScript comments explain declarations and dashboard behaviour.
- TOML, YAML, Dockerfile, `.env.example`, and `.gitignore`: comments explain each active configuration entry or rule.
- Tests: comments explain what each test/setup statement is doing. Tests are part of the project because they define expected behaviour.

## Suggested learning order
1. `src/mcp_canarytrap/phase1_design.py`
2. `src/mcp_canarytrap/events.py`
3. `src/mcp_canarytrap/verdict.py`
4. `src/mcp_canarytrap/harness.py`
5. `src/mcp_canarytrap/storage.py`
6. `src/mcp_canarytrap/api.py`
7. `src/mcp_canarytrap/gateway_core.py`
8. `src/mcp_canarytrap/http_gateway.py`
9. `src/mcp_canarytrap/stdio_proxy.py`
10. `src/mcp_canarytrap/security_center.py`
11. `src/mcp_canarytrap/templates/index.html`

The comments explain the code, but you should still run the application and tests. A comment does not prove that a feature works. The supplied code is a prototype; its supported traffic paths and documented limitations still apply.
