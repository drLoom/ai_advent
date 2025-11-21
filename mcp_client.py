"""Minimal MCP client for retrieving available tools."""
import asyncio
import logging
from typing import List, Dict, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """Minimal MCP client to connect and retrieve tools."""

    def __init__(self, server_script: Optional[str] = None):
        """
        Initialize MCP client.

        Args:
            server_script: Path to MCP server script
        """
        self.server_script = server_script or "mcp_server_filesystem.py"
        self.connected = False
        self.tools = []
        self.session: Optional[ClientSession] = None
        self._cleanup_task = None

    def connect(self) -> bool:
        """
        Establish connection to MCP server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MCP server: {self.server_script}")

            # Run connection in async context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(self._connect_async())
                self.connected = True
                logger.info("MCP connection established")
                return True
            finally:
                # Don't close the loop, we need it for subsequent calls
                pass

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.connected = False
            return False

    async def _connect_async(self):
        """Async connection logic."""
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python3", self.server_script],
        )

        # Store server params for later use
        self.server_params = server_params

    def get_tools(self) -> List[Dict]:
        """
        Retrieve list of available tools from MCP server.

        Returns:
            List of tool definitions
        """
        if not self.connected:
            logger.warning("Not connected to MCP server")
            return []

        try:
            # Create new event loop for this thread
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(self._get_tools_async())

        except Exception as e:
            logger.error(f"Failed to retrieve tools: {e}")
            return []

    async def _get_tools_async(self) -> List[Dict]:
        """Async tool retrieval."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.list_tools()

                self.tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                    for tool in result.tools
                ]

                logger.info(
                    f"Retrieved {len(self.tools)} tools from MCP server"
                )
                return self.tools

    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        Call a tool with given arguments.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self.connected:
            logger.warning("Not connected to MCP server")
            return {"error": "Not connected to MCP server"}

        try:
            # Create new event loop for this thread
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(
                self._call_tool_async(tool_name, arguments)
            )

        except Exception as e:
            logger.error(f"Failed to call tool: {e}")
            return {"error": str(e)}

    async def _call_tool_async(
        self, tool_name: str, arguments: Dict
    ) -> Dict:
        """Async tool calling."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(tool_name, arguments)

                # Extract text content from result
                content = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        content.append(item.text)

                logger.info(f"Tool {tool_name} executed successfully")
                return {
                    "success": True,
                    "result": "\n".join(content)
                }

    def disconnect(self):
        """Disconnect from MCP server."""
        if self.connected:
            logger.info("Disconnecting from MCP server")
            self.connected = False
            self.session = None
