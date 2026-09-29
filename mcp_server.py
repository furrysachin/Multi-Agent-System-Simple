import asyncio

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("travel-tools")


@mcp.tool()
async def search_flights_tool(query: str) -> str:
    """Search live flight information for a travel query."""
    from tools.flight_tool import search_flights

    return await asyncio.to_thread(search_flights, query)


@mcp.tool()
async def search_hotels_tool(query: str) -> str:
    """Search for useful hotel information for a travel query."""
    from tools.tavily_tool import tavily_search

    return await asyncio.to_thread(tavily_search, f"Best hotels for {query}")


if __name__ == "__main__":
    mcp.run(transport="stdio")
