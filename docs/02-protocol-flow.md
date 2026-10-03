# Protocol Flow

## stdio

```text
Client process --stdin/stdout--> MCP server subprocess
```

## Lifecycle

```text
construct Client -> enter context -> initialize/negotiate -> discover -> requests -> leave context
```

## Discovery

The learning client uses:
- `list_tools()`
- `list_resources()`
- `list_resource_templates()`
- `list_prompts()`

## Execution

```text
Client --call tool--> Server --result--> Client
Client --read resource--> Server --contents--> Client
Client --get prompt--> Server --messages--> Client
```

This is the communication vocabulary needed before implementing the future interaction logger.
