"""Manager for handling multiple MCP clients."""
import logging
from typing import List, Dict, Optional
from .client import MCPClient

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Manages multiple MCP clients and aggregates their tools."""

    def __init__(self, server_scripts: List[str]):
        """
        Initialize MCP client manager with multiple servers.

        Args:
            server_scripts: List of MCP server script paths
        """
        self.clients: Dict[str, MCPClient] = {}
        self.connected = False

        for script in server_scripts:
            client_name = script.split('/')[-1].replace('.py', '')
            self.clients[client_name] = MCPClient(script)

    def connect(self) -> bool:
        """
        Connect to all MCP servers.

        Returns:
            True if all connections successful, False otherwise
        """
        success = True
        for name, client in self.clients.items():
            try:
                if client.connect():
                    logger.info(f"Connected to MCP server: {name}")
                else:
                    logger.error(f"Failed to connect to MCP server: {name}")
                    success = False
            except Exception as e:
                logger.error(f"Error connecting to {name}: {e}")
                success = False

        self.connected = success
        return success

    def get_tools(self) -> List[Dict]:
        """
        Get aggregated tools from all connected clients.

        Returns:
            List of all available tools from all servers (deduplicated)
        """
        all_tools = []
        seen_names = set()

        for name, client in self.clients.items():
            try:
                if client.connected:
                    tools = client.get_tools()
                    # Deduplicate tools by name
                    for tool in tools:
                        tool_name = tool.get('name')
                        if tool_name and tool_name not in seen_names:
                            all_tools.append(tool)
                            seen_names.add(tool_name)
                    logger.info(f"Loaded {len(tools)} tools from {name}")
            except Exception as e:
                logger.error(f"Error getting tools from {name}: {e}")

        logger.info(f"Total unique tools: {len(all_tools)}")
        return all_tools

    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        Call a tool by searching through all clients.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found in any client
        """
        for name, client in self.clients.items():
            if not client.connected:
                continue

            tools = client.get_tools()
            tool_names = [t.get('name') for t in tools]

            if tool_name in tool_names:
                logger.info(f"Calling tool '{tool_name}' via {name}")
                return client.call_tool(tool_name, arguments)

        raise ValueError(f"Tool '{tool_name}' not found in any connected MCP server")

    def disconnect(self):
        """Disconnect all MCP clients."""
        for name, client in self.clients.items():
            try:
                if hasattr(client, 'disconnect'):
                    client.disconnect()
                logger.info(f"Disconnected from {name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {name}: {e}")

        self.connected = False

    def get_server_status(self) -> Dict[str, bool]:
        """
        Get connection status of all servers.

        Returns:
            Dictionary mapping server names to connection status
        """
        return {name: client.connected for name, client in self.clients.items()}
