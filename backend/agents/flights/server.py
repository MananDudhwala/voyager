"""
Flight Agent MCP Server.

Exposes search_flights and get_flight_details as MCP tools.

Run standalone:
    python -m agents.flights.server
"""

from __future__ import annotations

import mcp.server.stdio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

from agents.flights.tools import search_flights, get_flight_details

app = Server("flight-agent")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_flights",
            description=(
                "Search for available flights between two cities on a given date. "
                "Returns up to 10 options sorted by price. "
                "Pass max_price to filter by budget."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin city or IATA code (e.g. 'JFK', 'New York')",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination city or IATA code (e.g. 'CDG', 'Paris')",
                    },
                    "date": {
                        "type": "string",
                        "description": "Departure date in YYYY-MM-DD format",
                    },
                    "passengers": {
                        "type": "integer",
                        "description": "Number of passengers (default 1)",
                        "default": 1,
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum total price in USD for all passengers (optional)",
                    },
                },
                "required": ["origin", "destination", "date"],
            },
        ),
        Tool(
            name="get_flight_details",
            description=(
                "Retrieve full details for a specific flight by its ID, "
                "including baggage policy, number of stops, and available seats."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "flight_id": {
                        "type": "string",
                        "description": "The unique flight identifier from search_flights",
                    }
                },
                "required": ["flight_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "search_flights":
            result = search_flights(
                origin=arguments["origin"],
                destination=arguments["destination"],
                date=arguments["date"],
                passengers=arguments.get("passengers", 1),
                max_price=arguments.get("max_price"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_flight_details":
            result = get_flight_details(flight_id=arguments["flight_id"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


if __name__ == "__main__":
    import asyncio

    async def _main():
        async with stdio_server() as (read, write):
            await app.run(read, write, app.create_initialization_options())

    asyncio.run(_main())
