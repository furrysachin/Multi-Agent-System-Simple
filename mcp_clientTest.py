import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_PATH = Path(__file__).with_name("mcp_server.py")


async def main() -> None:
	server_parameters = StdioServerParameters(
		command=sys.executable,
		args=[str(SERVER_PATH)],
	)

	async with stdio_client(server_parameters) as (read_stream, write_stream):
		async with ClientSession(read_stream, write_stream) as session:
			await session.initialize()

			tools = await session.list_tools()
			print("Available tools:")
			for tool in tools.tools:
				print(f"- {tool.name}: {tool.description or 'No description'}")

			flight_result = await session.call_tool(
				"search_flights_tool",
				{"query": "Flights from Dhaka to Delhi"},
			)
			print("\nFlight search result:")
			print(flight_result.content)


if __name__ == "__main__":
	asyncio.run(main())
