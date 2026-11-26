import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent / "mcp_server.py"

async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    print("\\nConnecting to MCP-CanaryTrap...")
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("Connected successfully.")
            listed = await session.list_tools()
            print("\\nAvailable tools:")
            for tool in listed.tools:
                print(f"- {tool.name}: {tool.description or ''}")
            name = input("\\nEnter tool name (or q to quit): ").strip()
            if name.lower() == "q":
                return
            if name not in {tool.name for tool in listed.tools}:
                print("Tool not found.")
                return
            args = {"city": input("Enter city: ").strip() or "Haridwar"} if name == "weather_search" else {}
            result = await session.call_tool(name, arguments=args)
            print("\\nMCP tool response:")
            for item in result.content:
                if getattr(item, "text", None):
                    print(item.text)
            if result.is_error:
                print("The MCP server reported a tool error.")

if __name__ == "__main__":
    asyncio.run(main())
