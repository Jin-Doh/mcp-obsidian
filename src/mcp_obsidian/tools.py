"""Tool handlers for MCP-Obsidian server implementation."""

import json
import os
from collections.abc import Sequence

from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

from . import obsidian

api_key = os.getenv("OBSIDIAN_API_KEY", "")
if api_key == "":
    raise ValueError(
        f"OBSIDIAN_API_KEY environment variable required. Working directory: {os.getcwd()}"
    )

TOOL_LIST_FILES_IN_VAULT = "obsidian_list_files_in_vault"
TOOL_LIST_FILES_IN_DIR = "obsidian_list_files_in_dir"


class ToolHandler:
    """Base class for tool handlers."""

    def __init__(self, tool_name: str):
        """Initialize the tool handler.

        Args:
            tool_name: Name of the tool
        """
        self.name = tool_name

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError()

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the tool with given arguments.

        Args:
            args: Tool arguments

        Returns:
            Tool execution results

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError()


class ListFilesInVaultToolHandler(ToolHandler):
    """Handler for listing files in the Obsidian vault."""

    def __init__(self):
        """Initialize the list files in vault tool handler."""
        super().__init__(TOOL_LIST_FILES_IN_VAULT)

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="Lists all files and directories in the root directory of your Obsidian vault.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the list files in vault tool.

        Args:
            args: Tool arguments (none required)

        Returns:
            List of files in the vault root
        """
        api = obsidian.Obsidian(api_key=api_key)
        files = api.list_files_in_vault()
        return [TextContent(type="text", text=json.dumps(files, indent=2))]


class ListFilesInDirToolHandler(ToolHandler):
    """Handler for listing files in a specific directory."""

    def __init__(self):
        """Initialize the list files in directory tool handler."""
        super().__init__(TOOL_LIST_FILES_IN_DIR)

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="Lists all files and directories that exist in a specific Obsidian directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dirpath": {
                        "type": "string",
                        "description": "Path to list files from (relative to your vault root). Note that empty directories will not be returned.",
                    },
                },
                "required": ["dirpath"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the list files in directory tool.

        Args:
            args: Tool arguments including dirpath

        Returns:
            List of files in the specified directory

        Raises:
            RuntimeError: If dirpath argument is missing
        """
        if "dirpath" not in args:
            raise RuntimeError("dirpath argument missing in arguments")
        api = obsidian.Obsidian(api_key=api_key)
        files = api.list_files_in_dir(args["dirpath"])
        return [TextContent(type="text", text=json.dumps(files, indent=2))]


class GetFileContentsToolHandler(ToolHandler):
    """Handler for getting file contents."""

    def __init__(self):
        """Initialize the get file contents tool handler."""
        super().__init__("obsidian_get_file_contents")

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="Return the content of a single file in your vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the relevant file (relative to your vault root).",
                        "format": "path",
                    },
                },
                "required": ["filepath"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the get file contents tool.

        Args:
            args: Tool arguments including filepath

        Returns:
            Content of the specified file

        Raises:
            RuntimeError: If filepath argument is missing
        """
        if "filepath" not in args:
            raise RuntimeError("filepath argument missing in arguments")
        api = obsidian.Obsidian(api_key=api_key)
        content = api.get_file_contents(args["filepath"])
        return [TextContent(type="text", text=json.dumps(content, indent=2))]


class SearchToolHandler(ToolHandler):
    """Handler for simple text search."""

    def __init__(self):
        """Initialize the search tool handler."""
        super().__init__("obsidian_simple_search")

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="""Simple search for documents matching a specified text query across all files in the vault.
            Use this tool when you want to do a simple text search""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to a simple search for in the vault.",
                    },
                    "context_length": {
                        "type": "integer",
                        "description": "How much context to return around the matching string (default: 100)",
                        "default": 100,
                    },
                },
                "required": ["query"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the search tool.

        Args:
            args: Tool arguments including query and optional context_length

        Returns:
            Search results with context

        Raises:
            RuntimeError: If query argument is missing
        """
        if "query" not in args:
            raise RuntimeError("query argument missing in arguments")
        context_length = args.get("context_length", 100)
        api = obsidian.Obsidian(api_key=api_key)
        results = api.search(args["query"], context_length)
        formatted_results = []
        for result in results:
            formatted_matches = []
            for match in result.get("matches", []):
                context = match.get("context", "")
                match_pos = match.get("match", {})
                start = match_pos.get("start", 0)
                end = match_pos.get("end", 0)
                formatted_matches.append(
                    {"context": context, "match_position": {"start": start, "end": end}}
                )
            formatted_results.append(
                {
                    "filename": result.get("filename", ""),
                    "score": result.get("score", 0),
                    "matches": formatted_matches,
                }
            )
        return [TextContent(type="text", text=json.dumps(formatted_results, indent=2))]


class AppendContentToolHandler(ToolHandler):
    """Handler for appending content to files."""

    def __init__(self):
        """Initialize the append content tool handler."""
        super().__init__("obsidian_append_content")

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="Append content to a new or existing file in the vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file (relative to vault root)",
                        "format": "path",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to append to the file",
                    },
                },
                "required": ["filepath", "content"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the append content tool.

        Args:
            args: Tool arguments including filepath and content

        Returns:
            Success message

        Raises:
            RuntimeError: If required arguments are missing
        """
        if "filepath" not in args or "content" not in args:
            raise RuntimeError("filepath and content arguments required")
        api = obsidian.Obsidian(api_key=api_key)
        api.append_content(args.get("filepath", ""), args["content"])
        return [
            TextContent(
                type="text", text=f"Successfully appended content to {args['filepath']}"
            )
        ]


class PatchContentToolHandler(ToolHandler):
    """Handler for patching content in files."""

    def __init__(self):
        """Initialize the patch content tool handler."""
        super().__init__("obsidian_patch_content")

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="Insert content into an existing note relative to a heading, block reference, or frontmatter field.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file (relative to vault root)",
                        "format": "path",
                    },
                    "operation": {
                        "type": "string",
                        "description": "Operation to perform (append, prepend, or replace)",
                        "enum": ["append", "prepend", "replace"],
                    },
                    "target_type": {
                        "type": "string",
                        "description": "Type of target to patch",
                        "enum": ["heading", "block", "frontmatter"],
                    },
                    "target": {
                        "type": "string",
                        "description": "Target identifier (heading path, block reference, or frontmatter field)",
                    },
                    "content": {"type": "string", "description": "Content to insert"},
                },
                "required": [
                    "filepath",
                    "operation",
                    "target_type",
                    "target",
                    "content",
                ],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the patch content tool.

        Args:
            args: Tool arguments including filepath, operation, target_type, target, and content

        Returns:
            Success message

        Raises:
            RuntimeError: If required arguments are missing
        """
        required = ["filepath", "operation", "target_type", "target", "content"]
        if not all(key in args for key in required):
            raise RuntimeError(f"Missing required arguments: {', '.join(required)}")
        api = obsidian.Obsidian(api_key=api_key)
        api.patch_content(
            args.get("filepath", ""),
            args.get("operation", ""),
            args.get("target_type", ""),
            args.get("target", ""),
            args.get("content", ""),
        )
        return [
            TextContent(
                type="text", text=f"Successfully patched content in {args['filepath']}"
            )
        ]


class ComplexSearchToolHandler(ToolHandler):
    """Handler for complex search using JsonLogic queries."""

    def __init__(self):
        """Initialize the complex search tool handler."""
        super().__init__("obsidian_complex_search")

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="""Complex search for documents using a JsonLogic query.
           Supports standard JsonLogic operators plus 'glob' and 'regexp' for pattern matching. Results must be non-falsy.
           Use this tool when you want to do a complex search, e.g. for all documents with certain tags etc.
           """,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "object",
                        "description": 'JsonLogic query object. Example: {"glob": ["*.md", {"var": "path"}]} matches all markdown files',
                    }
                },
                "required": ["query"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the complex search tool.

        Args:
            args: Tool arguments including query

        Returns:
            Search results

        Raises:
            RuntimeError: If query argument is missing
        """
        if "query" not in args:
            raise RuntimeError("query argument missing in arguments")
        api = obsidian.Obsidian(api_key=api_key)
        results = api.search_json(args.get("query", ""))
        return [TextContent(type="text", text=json.dumps(results, indent=2))]


class BatchGetFileContentsToolHandler(ToolHandler):
    """Handler for getting contents of multiple files."""

    def __init__(self):
        """Initialize the batch get file contents tool handler."""
        super().__init__("obsidian_batch_get_file_contents")

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="Return the contents of multiple files in your vault, concatenated with headers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepaths": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Path to a file (relative to your vault root)",
                            "format": "path",
                        },
                        "description": "List of file paths to read",
                    },
                },
                "required": ["filepaths"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the batch get file contents tool.

        Args:
            args: Tool arguments including filepaths

        Returns:
            Contents of all specified files

        Raises:
            RuntimeError: If filepaths argument is missing
        """
        if "filepaths" not in args:
            raise RuntimeError("filepaths argument missing in arguments")
        api = obsidian.Obsidian(api_key=api_key)
        content = api.get_batch_file_contents(args["filepaths"])
        return [TextContent(type="text", text=content)]


class PeriodicNotesToolHandler(ToolHandler):
    """Handler for getting periodic notes."""

    def __init__(self):
        """Initialize the periodic notes tool handler."""
        super().__init__("obsidian_get_periodic_note")

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="Get current periodic note for the specified period.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "The period type (daily, weekly, monthly, quarterly, yearly)",
                        "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"],
                    }
                },
                "required": ["period"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the periodic notes tool.

        Args:
            args: Tool arguments including period

        Returns:
            Content of the periodic note

        Raises:
            RuntimeError: If period argument is missing or invalid
        """
        if "period" not in args:
            raise RuntimeError("period argument missing in arguments")
        period = args["period"]
        valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        if period not in valid_periods:
            raise RuntimeError(
                f"Invalid period: {period}. Must be one of: {', '.join(valid_periods)}"
            )
        api = obsidian.Obsidian(api_key=api_key)
        content = api.get_periodic_note(period)
        return [TextContent(type="text", text=content)]


class RecentPeriodicNotesToolHandler(ToolHandler):
    """Handler for getting recent periodic notes."""

    def __init__(self):
        """Initialize the recent periodic notes tool handler."""
        super().__init__("obsidian_get_recent_periodic_notes")

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="Get most recent periodic notes for the specified period type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "The period type (daily, weekly, monthly, quarterly, yearly)",
                        "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of notes to return (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "include_content": {
                        "type": "boolean",
                        "description": "Whether to include note content (default: false)",
                        "default": False,
                    },
                },
                "required": ["period"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the recent periodic notes tool.

        Args:
            args: Tool arguments including period

        Returns:
            List of recent periodic notes

        Raises:
            RuntimeError: If period argument is missing or invalid, or if limit is invalid
        """
        if "period" not in args:
            raise RuntimeError("period argument missing in arguments")
        period = args["period"]
        valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        if period not in valid_periods:
            raise RuntimeError(
                f"Invalid period: {period}. Must be one of: {', '.join(valid_periods)}"
            )

        limit = args.get("limit", 5)
        if not isinstance(limit, int) or limit < 1:
            raise RuntimeError(f"Invalid limit: {limit}. Must be a positive integer")

        include_content = args.get("include_content", False)
        if not isinstance(include_content, bool):
            raise RuntimeError(
                f"Invalid include_content: {include_content}. Must be a boolean"
            )

        api = obsidian.Obsidian(api_key=api_key)
        results = api.get_recent_periodic_notes(period, limit, include_content)
        return [TextContent(type="text", text=json.dumps(results, indent=2))]


class RecentChangesToolHandler(ToolHandler):
    """Handler for getting recently modified files."""

    def __init__(self):
        """Initialize the recent changes tool handler."""
        super().__init__("obsidian_get_recent_changes")

    def get_tool_description(self) -> Tool:
        """Get the tool's description.

        Returns:
            Tool description
        """
        return Tool(
            name=self.name,
            description="Get recently modified files in the vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of files to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "days": {
                        "type": "integer",
                        "description": "Only include files modified within this many days (default: 90)",
                        "minimum": 1,
                        "default": 90,
                    },
                },
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Run the recent changes tool.

        Args:
            args: Tool arguments including optional limit and days

        Returns:
            List of recently modified files

        Raises:
            RuntimeError: If limit or days arguments are invalid
        """
        limit = args.get("limit", 10)
        if not isinstance(limit, int) or limit < 1:
            raise RuntimeError(f"Invalid limit: {limit}. Must be a positive integer")

        days = args.get("days", 90)
        if not isinstance(days, int) or days < 1:
            raise RuntimeError(f"Invalid days: {days}. Must be a positive integer")

        api = obsidian.Obsidian(api_key=api_key)
        results = api.get_recent_changes(limit, days)
        return [TextContent(type="text", text=json.dumps(results, indent=2))]
