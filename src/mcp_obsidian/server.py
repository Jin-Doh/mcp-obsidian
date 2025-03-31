"""MCP-Obsidian server implementation for handling Obsidian API requests."""

import logging
import os
from collections.abc import Sequence
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

from . import tools

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-obsidian")

api_key = os.getenv("OBSIDIAN_API_KEY")
if not api_key:
    raise ValueError(
        "OBSIDIAN_API_KEY environment variable required. "
        f"Working directory: {os.getcwd()}"
    )

app = Server("mcp-obsidian")
tool_handlers = {}


def add_tool_handler(tool_class: tools.ToolHandler) -> None:
    """Add a tool handler to the global tool handlers dictionary.

    Args:
        tool_class: The tool handler class to add
    """
    global tool_handlers
    tool_handlers[tool_class.name] = tool_class


def get_tool_handler(name: str) -> tools.ToolHandler | None:
    """Get a tool handler by name.

    Args:
        name: The name of the tool handler to retrieve

    Returns:
        The tool handler instance or None if not found
    """
    if name not in tool_handlers:
        return None
    return tool_handlers[name]


# Register tool handlers
add_tool_handler(tools.ListFilesInDirToolHandler())
add_tool_handler(tools.ListFilesInVaultToolHandler())
add_tool_handler(tools.GetFileContentsToolHandler())
add_tool_handler(tools.SearchToolHandler())
add_tool_handler(tools.PatchContentToolHandler())
add_tool_handler(tools.AppendContentToolHandler())
add_tool_handler(tools.ComplexSearchToolHandler())
add_tool_handler(tools.BatchGetFileContentsToolHandler())
add_tool_handler(tools.PeriodicNotesToolHandler())
add_tool_handler(tools.RecentPeriodicNotesToolHandler())
add_tool_handler(tools.RecentChangesToolHandler())


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools.

    Returns:
        List of available tool descriptions
    """
    return [th.get_tool_description() for th in tool_handlers.values()]


@app.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for command line run.

    Args:
        name: The name of the tool to call
        arguments: The arguments to pass to the tool

    Returns:
        The result of the tool execution

    Raises:
        RuntimeError: If arguments are invalid or tool execution fails
        ValueError: If the tool is not found
    """
    if not isinstance(arguments, dict):
        raise RuntimeError("arguments must be dictionary")

    tool_handler = get_tool_handler(name)
    if not tool_handler:
        raise ValueError(f"Unknown tool: {name}")

    try:
        return tool_handler.run_tool(arguments)
    except Exception as e:
        logger.error(str(e))
        raise RuntimeError(f"Caught Exception. Error: {str(e)}")


async def main():
    """Main entry point for the server."""
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )
