"""MCP server management and tool integration."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import settings
from core.types import MCPTool

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages MCP server lifecycle and tool discovery."""

    def __init__(self):
        """Initialize the MCP manager."""
        self.servers: Dict[str, subprocess.Popen] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, List[MCPTool]] = {}
        self.initialized = False

    async def initialize(self) -> None:
        """Start all configured MCP servers and discover tools."""
        if self.initialized:
            return

        logger.info("Initializing MCP servers...")

        # Start Atlassian MCP if configured
        if settings.has_jira_config() or settings.has_confluence_config():
            await self._start_atlassian_server()

        # Start Slack MCP if configured
        if settings.has_slack_config():
            await self._start_slack_server()

        # Start GitHub CI MCP if configured
        if settings.has_github_ci_config():
            await self._start_github_ci_server()

        # Discover tools from all servers
        await self._discover_tools()

        self.initialized = True
        logger.info(f"MCP manager initialized with {len(self.tools)} tool sets")

    async def _start_atlassian_server(self) -> None:
        """Start Atlassian MCP server and establish client session."""
        try:
            config_path = Path("mcp_servers/atlassian_config.json")

            if not config_path.exists():
                logger.warning("Atlassian MCP config not found, skipping")
                return

            with open(config_path) as f:
                config = json.load(f)

            # Prepare environment variables
            env = {
                "JIRA_URL": settings.jira_url or "",
                "JIRA_EMAIL": settings.jira_email or "",
                "JIRA_API_TOKEN": settings.jira_api_token or "",
                "CONFLUENCE_URL": settings.confluence_url or "",
                "CONFLUENCE_EMAIL": settings.confluence_email or "",
                "CONFLUENCE_API_TOKEN": settings.confluence_api_token or "",
            }

            # Create server parameters for MCP protocol
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "mcp_atlassian"],
                env={**os.environ, **env}
            )

            # Start server and create session using MCP protocol
            read, write = await stdio_client(server_params)
            session = ClientSession(read, write)
            await session.initialize()

            self.sessions["atlassian"] = session
            logger.info("Atlassian MCP server connected")

        except Exception as e:
            logger.error(f"Failed to start Atlassian MCP server: {e}")

    async def _start_slack_server(self) -> None:
        """Start Slack MCP server and establish client session."""
        try:
            config_path = Path("mcp_servers/slack_config.json")

            if not config_path.exists():
                logger.warning("Slack MCP config not found, skipping")
                return

            with open(config_path) as f:
                config = json.load(f)

            # Prepare environment variables
            env = {
                "SLACK_BOT_TOKEN": settings.slack_bot_token or "",
                "SLACK_APP_TOKEN": settings.slack_app_token or "",
            }

            # Create server parameters for MCP protocol
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "slack_mcp"],
                env={**os.environ, **env}
            )

            # Start server and create session using MCP protocol
            read, write = await stdio_client(server_params)
            session = ClientSession(read, write)
            await session.initialize()

            self.sessions["slack"] = session
            logger.info("Slack MCP server connected")

        except Exception as e:
            logger.error(f"Failed to start Slack MCP server: {e}")

    async def _start_github_ci_server(self) -> None:
        """Start GitHub CI MCP server and establish client session."""
        try:
            config_path = Path("mcp_servers/github_ci_config.json")

            if not config_path.exists():
                logger.warning("GitHub CI MCP config not found, skipping")
                return

            with open(config_path) as f:
                config = json.load(f)

            # Prepare environment variables
            env = {
                "GITHUB_TOKEN": settings.github_token or "",
                "GITHUB_OWNER": settings.github_owner or "",
                "GITHUB_REPO": settings.github_repo or "",
            }

            # Create server parameters for MCP protocol
            # Note: This assumes a github_mcp package/server exists
            # You may need to implement or use an existing GitHub MCP server
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "github_mcp"],
                env={**os.environ, **env}
            )

            # Start server and create session using MCP protocol
            read, write = await stdio_client(server_params)
            session = ClientSession(read, write)
            await session.initialize()

            self.sessions["github_ci"] = session
            logger.info("GitHub CI MCP server connected")

        except Exception as e:
            logger.error(f"Failed to start GitHub CI MCP server: {e}")

    async def _discover_tools(self) -> None:
        """Discover tools from all connected MCP servers via MCP protocol."""
        self.tools.clear()

        for server_name, session in self.sessions.items():
            try:
                # Use MCP protocol to list tools
                tools_result = await session.list_tools()

                # Convert to MCPTool objects
                server_tools = []
                for tool_info in tools_result.tools:
                    server_tools.append(MCPTool(
                        name=tool_info.name,
                        description=tool_info.description,
                        input_schema=tool_info.inputSchema,
                        server=server_name
                    ))

                self.tools[server_name] = server_tools
                logger.info(f"Discovered {len(server_tools)} tools from {server_name}")

            except Exception as e:
                logger.error(f"Failed to discover tools from {server_name}: {e}")

    async def call_tool(
        self,
        server: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Execute a tool on the specified MCP server via MCP protocol.

        Args:
            server: Server name
            tool_name: Tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ValueError: If server not found
            Exception: If tool call fails
        """
        if server not in self.sessions:
            raise ValueError(f"MCP server '{server}' not connected")

        session = self.sessions[server]

        try:
            logger.info(f"Calling {server}.{tool_name}")
            logger.debug(f"Arguments: {arguments}")

            # Call tool via MCP protocol
            result = await session.call_tool(tool_name, arguments)

            logger.debug(f"Tool result: {result}")
            return result

        except Exception as e:
            logger.error(f"Tool call failed for {server}.{tool_name}: {e}")
            raise

    def get_all_tools(self) -> List[MCPTool]:
        """Get all available tools from all servers.

        Returns:
            List of all tools
        """
        all_tools = []
        for server_tools in self.tools.values():
            all_tools.extend(server_tools)
        return all_tools

    def get_tools_for_server(self, server: str) -> List[MCPTool]:
        """Get tools for a specific server.

        Args:
            server: Server name

        Returns:
            List of tools for that server
        """
        return self.tools.get(server, [])

    async def shutdown(self) -> None:
        """Shutdown all MCP servers gracefully."""
        logger.info("Shutting down MCP servers...")

        # Close MCP sessions first
        for server_name, session in self.sessions.items():
            try:
                await session.close()
                logger.info(f"Closed {server_name} session")
            except Exception as e:
                logger.error(f"Error closing {server_name} session: {e}")

        # Then terminate any remaining processes (if direct process management was used)
        for server_name, process in self.servers.items():
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
                logger.info(f"Terminated {server_name} process")
            except asyncio.TimeoutError:
                logger.warning(f"Force killing {server_name} process")
                process.kill()
            except Exception as e:
                logger.error(f"Error shutting down {server_name} process: {e}")

        self.sessions.clear()
        self.servers.clear()
        self.tools.clear()
        self.initialized = False
