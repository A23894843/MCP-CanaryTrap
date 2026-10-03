import asyncio
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters

SERVER_FILE = Path(__file__).with_name("server.py")

async def main() -> None:
    server = StdioServerParameters(command=sys.executable, args=[str(SERVER_FILE)])
    async with Client(server) as client:
        print("=== MCP SESSION ===")
        print("Server:", client.server_info.name if client.server_info else "unknown")
        print("Protocol version:", client.protocol_version)
        print("Capabilities:", client.server_capabilities)

        tools = await client.list_tools()
        print("\nTools:")
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description or ''}")

        resources = await client.list_resources()
        print("\nResources:")
        for resource in resources.resources:
            print(f"  - {resource.uri}: {resource.description or ''}")

        templates = await client.list_resource_templates()
        print("\nResource templates:")
        for template in templates.resource_templates:
            print(f"  - {template.uri_template}: {template.description or ''}")

        prompts = await client.list_prompts()
        print("\nPrompts:")
        for prompt in prompts.prompts:
            print(f"  - {prompt.name}: {prompt.description or ''}")

        result = await client.call_tool("search_employee", {"employee_id": "1024"})
        print("\nTool result:")
        for item in result.content:
            if hasattr(item, "text"):
                print(" ", item.text)

        resource_result = await client.read_resource("employee://profile/1024")
        print("\nResource result:")
        for item in resource_result.contents:
            if hasattr(item, "text"):
                print(item.text)

        prompt_result = await client.get_prompt("find_employee", {"employee_id": "1024"})
        print("\nPrompt result:")
        for message in prompt_result.messages:
            print(" ", message)

if __name__ == "__main__":
    asyncio.run(main())
