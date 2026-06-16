"""
Itinerary Agent MCP Server.

Exposes get_pois, get_weather, get_travel_times, and build_itinerary as MCP tools.

Run standalone:
    python -m agents.itinerary.server
"""

from __future__ import annotations

import json
import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from agents.itinerary.tools import get_pois, get_weather, get_travel_times, build_itinerary

app = Server("itinerary-agent")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_pois",
            description=(
                "Retrieve points of interest for a city, optionally filtered by category. "
                "Results are sorted by rating. Use indoor_only=true on rainy forecast days."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name (e.g. 'Paris')"},
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by category: museum|park|restaurant|landmark|beach|shopping|entertainment|religious|sport",
                    },
                    "limit": {"type": "integer", "default": 10, "description": "Max results (1-50)"},
                    "indoor_only": {"type": "boolean", "default": False},
                },
                "required": ["city"],
            },
        ),
        Tool(
            name="get_weather",
            description="Get daily weather forecast for a city across a list of dates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "dates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of dates in YYYY-MM-DD format",
                    },
                },
                "required": ["city", "dates"],
            },
        ),
        Tool(
            name="get_travel_times",
            description=(
                "Estimate travel time and distance between two named locations. "
                "Modes: walking | driving | transit."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "origin_name": {"type": "string"},
                    "destination_name": {"type": "string"},
                    "mode": {
                        "type": "string",
                        "enum": ["walking", "driving", "transit"],
                        "default": "walking",
                    },
                },
                "required": ["origin_name", "destination_name"],
            },
        ),
        Tool(
            name="build_itinerary",
            description=(
                "Build a complete day-by-day itinerary for a city. "
                "Automatically substitutes indoor POIs on rainy forecast days. "
                "Returns each day's POIs, weather, travel legs, and activity costs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "dates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "One date per day in YYYY-MM-DD format",
                    },
                    "pois": {
                        "type": "array",
                        "description": "POI objects returned from get_pois",
                    },
                    "travel_mode": {
                        "type": "string",
                        "enum": ["walking", "driving", "transit"],
                        "default": "walking",
                    },
                },
                "required": ["city", "dates", "pois"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_pois":
            result = get_pois(
                city=arguments["city"],
                categories=arguments.get("categories"),
                limit=arguments.get("limit", 10),
                indoor_only=arguments.get("indoor_only", False),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_weather":
            result = get_weather(city=arguments["city"], dates=arguments["dates"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_travel_times":
            result = get_travel_times(
                origin_name=arguments["origin_name"],
                destination_name=arguments["destination_name"],
                mode=arguments.get("mode", "walking"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "build_itinerary":
            result = build_itinerary(
                city=arguments["city"],
                dates=arguments["dates"],
                pois=arguments["pois"],
                travel_mode=arguments.get("travel_mode", "walking"),
            )
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
