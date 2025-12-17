import websockets
import threading
import asyncio
import logging
import random
import json
from utils import gen_tool_description

logger = logging.getLogger(__name__)

class xiaozhiconn(threading.Thread):
    def __init__(self, socketurl, is_reconnect=True):
        threading.Thread.__init__(self)
        self.socketurl = socketurl
        self.socket = None
        self.auto_reconnect = is_reconnect
        self.initial_delay = 1 # seconds
        self.max_delay = 60 # seconds
        self.protocol_version = "2024-11-05"
        self.daemon = True  # Allow thread to exit when main program exits

    async def mcp_proto_initialize(self):
        """Return the JSON-RPC initialize response."""
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name":    "socket-mcp-server",
                "version": "1.0.0"
            }
        }
    
    async def mcp_proto_list_tools(self):
        """Return the list of available tools."""
        return {"tools": gen_tool_description()}

    async def mcp_proto_call_tool(self, name: str, arguments: dict):
        """Execute a tool call and return the result."""
        # Placeholder for actual tool execution logic
        return {"status": "success", "tool": name, "arguments": arguments}

    def run(self):
        asyncio.run(self.connect_with_infinite_retry())

    async def reset(self):
        if self.socket is not None:
            try:
                await self.socket.close()
            except:
                pass
            self.socket = None

    async def connect_with_infinite_retry(self):
        delay = 0 if self.auto_reconnect else self.initial_delay

        attempt = 1
        while True:
            try:
                # Close existing connection if any
                await self.reset()
                logger.info(f"Connecting to {self.socketurl} (attempt {attempt}) …")
                # Connect to WebSocket (token is already in the URL)
                self.socket = await websockets.connect(
                    self.socketurl,
                    ping_interval=20,
                    ping_timeout=10
                )
                logger.info("[mcp] WebSocket connected successfully")
                
                # Handle messages in the WebSocket
                await self.handle_websocket_messages()
                
                # If we reach here, the connection was closed
                logger.info("[mcp] WebSocket connection ended")
                return

            except websockets.exceptions.WebSocketException as e:
                logger.error(f"[mcp] WebSocket error: {e}")
            except Exception as e:
                logger.error(f"[mcp] Connection error: {e}")

            if delay == 0:
                # For immediate reconnect, no sleep
                pass
            else:
                jitter = random.uniform(0.8, 1.2)
                wait = delay * jitter
                logger.info(f"[mcp] Retrying in {wait:.1f}s …")
                await asyncio.sleep(wait)

            delay = min(delay * 2, self.max_delay) if delay > 0 else 0
            attempt += 1

    async def handle_websocket_messages(self):
        """Handle incoming WebSocket messages and process MCP requests."""        
        logger.info("[mcp] WebSocket connected → ready to receive messages")        
        try:
            async for message in self.socket:
                try:
                    # Parse incoming JSON message
                    if isinstance(message, str):
                        payload = json.loads(message)
                    else:
                        payload = json.loads(message.decode('utf-8'))
                    
                    method = payload.get("method", "<unknown>")
                    logger.info(f"[mcp] Request received: {method}")
                    response = {"jsonrpc": "2.0", "id": payload.get("id")}

                    try:
                        if method == "initialize":
                            result = await self.mcp_proto_initialize()
                        elif method == "tools/list":
                            result = await self.mcp_proto_list_tools()
                        elif method == "tools/call":
                            params = payload.get("params", {}) or {}
                            name = params.get("name")
                            args = params.get("arguments", {}) or {}
                            logger.info(f"[mcp] Executing tool: {name}")
                            logger.debug(f"[mcp] {args}")
                            result = await self.mcp_proto_call_tool(name, args)
                            logger.debug(f"[mcp] Tool result {result}")
                        else:
                            raise ValueError(f"Unknown method: {method}")

                        response["result"] = result
                        logger.info(f"[mcp] Completed: {method}")

                    except Exception as e:
                        response["error"] = {"code": -32603, "message": str(e)}
                        logger.error(f"[mcp] Error in {method}:", e)
                    # Send response back through WebSocket
                    await self.socket.send(json.dumps(response))
                    
                except json.JSONDecodeError as e:
                    logger.error(f"[mcp] Invalid JSON received: {e}")
                except Exception as e:
                    logger.error(f"[mcp] Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("[mcp] WebSocket connection closed")
        except Exception as e:
            logger.error(f"[mcp] WebSocket error: {e}")