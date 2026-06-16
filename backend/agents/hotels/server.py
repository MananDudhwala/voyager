"""
Hotel Agent MCP Server.

Exposes search_hotels and get_hotel_details as MCP tools.

Run standalone:
    python -m agents.hotels.server
"""

from __future__ import annotations

import json
import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from agents.hotels.tools import search_hotels, get_hotel_details

app = Server("hotel-agent")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_hotels",
            description=(
                "Search for available hotels in a city for given check-in/check-out dates. "
                "Returns up to 10 options sorted by price per night. "
                "Optionally filter by max price or tier (budget/midscale/upscale/luxury)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Destination city name (e.g. 'Paris', 'Tokyo')",
                    },
                    "check_in": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format",
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format",
                    },
                    "guests": {
                        "type": "integer",
                        "description": "Number of guests (default 1)",
                        "default": 1,
                    },
                    "max_price_per_night": {
                        "type": "number",
                        "description": "Maximum price per night in USD (optional)",
                    },
                    "tier": {
                        "type": "string",
                        "enum": ["budget", "midscale", "upscale", "luxury"],
                        "description": "Hotel tier filter (optional)",
                    },
                },
                "required": ["city", "check_in", "check_out"],
            },
        ),
        Tool(
            name="get_hotel_details",
            description=(
                "Retrieve full details for a specific hotel by ID, "
                "including amenities, star rating, and cancellation policy."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hotel_id": {
                        "type": "string",
                        "description": "The unique hotel identifier from search_hotels",
                    }
                },
                "required": ["hotel_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "search_hotels":
            result = search_hotels(
                city=arguments["city"],
                check_in=arguments["check_in"],
                check_out=arguments["check_out"],
                guests=arguments.get("guests", 1),
                max_price_per_night=arguments.get("max_price_per_night"),
                tier=arguments.get("tier"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_hotel_details":
            result = get_hotel_details(hotel_id=arguments["hotel_id"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


if __name__ == "__main__":
    async def _main():
        async with stdio_server() as (read, write):
            await app.run(read, write, app.create_initialization_options())

    asyncio.run(_main())
