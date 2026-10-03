# MCP Fundamentals

```text
Host -> MCP Client -> MCP Server -> Tools / Resources / Prompts
```

- **Host:** application in which MCP functionality is used.
- **Client:** protocol participant that communicates with the server.
- **Server:** exposes capabilities to a client.
- **Tool:** action/capability the server can perform.
- **Resource:** readable information/context.
- **Prompt:** reusable message template selected/rendered through the client.

For CanaryTrap, the key distinction is:

```text
Static:  What does the server declare?
Runtime: What does the running server actually access?
```
