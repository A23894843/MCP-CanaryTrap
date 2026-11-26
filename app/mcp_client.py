import sys
import asyncio
from pathlib import Path
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

# Find the Project directory 
PROJECT_ROOT = Path (__file__).resolve().parent.parent

# Locate the MCP Server
SERVER_PATH = PROJECT_ROOT / "app" / "mcp_server.py"

async def main():
    # Configure the MCP Server process
    server_params = StdioServerParameters (
        command = sys.executable,
        args = [str(SERVER_PATH)]
    )

    print ("\nConnecting to MCP-CanaryTrap...")

    # Start the server and establish communication
    async with stdio_client (server_params) as (read, write):
        async with ClientSession (read, write) as session:
            # Initialize MCP connection
            await session.initialize()
            print ("Connected successfully!")

            # Retrieve available tools
            response = await session.list_tools()
            print ("\nAvailable MCP Tools:")
            for tool in response.tools:
                print ("-", tool.name)

            # Ask user to select a tool
            tool_name = input("\nEnter tool name: ").strip()
            available_tools = [tool.name for tool in response.tools]

            if tool_name not in available_tools:
                print ("Tool not found.")
                return

            # Prepare arguments
            arguments = {}
            if tool_name == "weather_search":
                city = input ("Enter city: ")
                arguments = {"city": city}

            # Execute the MCP tool
            print ("\nCalling MCP tool...")

            result = await session.call_tool(
                tool_name,
                arguments = arguments
            )

            print ("\nMCP Tool Response: ")
            for content in result.content:
                if hasattr (content, "text"):
                    print (content.text)

            if result.is_error:
                print ("The MCP server reported a tool error.")

if __name__ == "__main__":
    asyncio.run(main())