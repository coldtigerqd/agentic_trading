#!/usr/bin/env python3
"""
MCP Server for IBKR trading operations.

This server exposes IBKR trading functionality to Claude Code via the MCP protocol.
All operations include safety layer validation to prevent catastrophic errors.

Usage:
    python server.py

The server will listen on stdio for MCP protocol messages.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from tools import IBKRTools, TOOLS_METADATA


class MCPIBKRServer:
    """MCP server implementation for IBKR trading."""

    def __init__(self):
        self.tools = IBKRTools()
        self.server_info = {
            "name": "ibkr-trading",
            "version": "1.0.0",
            "description": "IBKR trading operations with safety layer"
        }

    async def handle_initialize(self, params: Dict) -> Dict:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": self.server_info,
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            }
        }

    async def handle_list_tools(self) -> List[Dict]:
        """Handle MCP tools/list request."""
        return TOOLS_METADATA

    async def handle_call_tool(self, name: str, arguments: Dict) -> Dict:
        """Handle MCP tools/call request."""
        try:
            # Route to appropriate tool (with async support)
            if name == "get_account":
                result = await self.tools.get_account_async()
            elif name == "get_positions":
                result = await self.tools.get_positions_async(**arguments)
            elif name == "place_order":
                result = await self.tools.place_order_async(**arguments)
            elif name == "close_position":
                result = self.tools.close_position(**arguments)
            elif name == "get_order_status":
                result = self.tools.get_order_status(**arguments)
            elif name == "health_check":
                result = await self.tools.health_check_async()
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Unknown tool: {name}"
                    }],
                    "isError": True
                }

            # Format response
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }

        except Exception as e:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error executing tool {name}: {str(e)}"
                }],
                "isError": True
            }

    async def handle_message(self, message: Dict) -> Optional[Dict]:
        """Handle incoming MCP protocol message."""
        method = message.get("method")

        if method == "initialize":
            result = await self.handle_initialize(message.get("params", {}))
            return {"result": result}

        elif method == "tools/list":
            tools = await self.handle_list_tools()
            return {"result": {"tools": tools}}

        elif method == "tools/call":
            params = message.get("params", {})
            result = await self.handle_call_tool(
                params.get("name"),
                params.get("arguments", {})
            )
            return {"result": result}

        elif method == "ping":
            return {"result": {"status": "ok"}}

        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    async def run(self):
        """Run the MCP server on stdio."""
        print("IBKR MCP Server starting...", file=sys.stderr)
        print(f"Server: {self.server_info['name']} v{self.server_info['version']}", file=sys.stderr)
        print("Listening on stdio for MCP messages...", file=sys.stderr)

        while True:
            try:
                # Read message from stdin (MCP protocol uses line-delimited JSON)
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    break

                # Parse JSON-RPC message
                message = json.loads(line.strip())

                # Handle message
                response = await self.handle_message(message)

                # Send response to stdout
                if response is not None:
                    response_obj = {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        **response
                    }
                    print(json.dumps(response_obj), flush=True)

            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)

            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                error_response = {
                    "jsonrpc": "2.0",
                    "id": message.get("id") if 'message' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)


def main():
    """Main entry point."""
    server = MCPIBKRServer()

    # Run the server
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
