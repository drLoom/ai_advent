#!/usr/bin/env python3
"""Simple MCP filesystem server."""
import asyncio
import os
from pathlib import Path
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server


app = Server("filesystem")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available filesystem tools."""
    return [
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to read"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="list_directory",
            description="List contents of a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    }
                },
                "required": ["path", "content"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool."""
    if name == "read_file":
        path = Path(arguments["path"])
        try:
            content = path.read_text()
            return [TextContent(type="text", text=content)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading file: {e}")]

    elif name == "list_directory":
        path = Path(arguments["path"])
        try:
            items = [item.name for item in path.iterdir()]
            return [TextContent(type="text", text="\n".join(items))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error listing directory: {e}")]

    elif name == "write_file":
        path = Path(arguments["path"])
        content = arguments["content"]
        try:
            path.write_text(content)
            return [TextContent(type="text", text=f"Successfully wrote to {path}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error writing file: {e}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
