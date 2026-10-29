# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Imports modules that this file uses.
import asyncio
# Explanation: Imports modules that this file uses.
import sys
# Explanation: Imports names from pathlib.
from pathlib import Path
# Explanation: Imports names from mcp.
from mcp import Client, StdioServerParameters

# Explanation: Sets a module-level constant or configuration value.
SERVER_FILE = Path(__file__).with_name("server.py")

# Explanation: Async function main: performs asynchronous work; inspect awaited calls and returned result.
async def main() -> None:
    # Explanation: Assigns or updates a value used later by this function or module.
    server = StdioServerParameters(command=sys.executable, args=[str(SERVER_FILE)])
    # Explanation: Asynchronously manage a resource and ensure its cleanup.
    async with Client(server) as client:
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("=== MCP SESSION ===")
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("Server:", client.server_info.name if client.server_info else "unknown")
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("Protocol version:", client.protocol_version)
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("Capabilities:", client.server_capabilities)

        # Explanation: Assigns or updates a value used later by this function or module.
        tools = await client.list_tools()
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("\nTools:")
        # Explanation: Loop over each item in the iterable and run the indented body.
        for tool in tools.tools:
            # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
            print(f"  - {tool.name}: {tool.description or ''}")

        # Explanation: Assigns or updates a value used later by this function or module.
        resources = await client.list_resources()
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("\nResources:")
        # Explanation: Loop over each item in the iterable and run the indented body.
        for resource in resources.resources:
            # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
            print(f"  - {resource.uri}: {resource.description or ''}")

        # Explanation: Assigns or updates a value used later by this function or module.
        templates = await client.list_resource_templates()
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("\nResource templates:")
        # Explanation: Loop over each item in the iterable and run the indented body.
        for template in templates.resource_templates:
            # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
            print(f"  - {template.uri_template}: {template.description or ''}")

        # Explanation: Assigns or updates a value used later by this function or module.
        prompts = await client.list_prompts()
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("\nPrompts:")
        # Explanation: Loop over each item in the iterable and run the indented body.
        for prompt in prompts.prompts:
            # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
            print(f"  - {prompt.name}: {prompt.description or ''}")

        # Explanation: Assigns or updates a value used later by this function or module.
        result = await client.call_tool("search_employee", {"employee_id": "1024"})
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("\nTool result:")
        # Explanation: Loop over each item in the iterable and run the indented body.
        for item in result.content:
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if hasattr(item, "text"):
                # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
                print(" ", item.text)

        # Explanation: Assigns or updates a value used later by this function or module.
        resource_result = await client.read_resource("employee://profile/1024")
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("\nResource result:")
        # Explanation: Loop over each item in the iterable and run the indented body.
        for item in resource_result.contents:
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if hasattr(item, "text"):
                # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
                print(item.text)

        # Explanation: Assigns or updates a value used later by this function or module.
        prompt_result = await client.get_prompt("find_employee", {"employee_id": "1024"})
        # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
        print("\nPrompt result:")
        # Explanation: Loop over each item in the iterable and run the indented body.
        for message in prompt_result.messages:
            # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
            print(" ", message)

# Explanation: Conditional decision: execute the following branch only when this expression is true.
if __name__ == "__main__":
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    asyncio.run(main())
