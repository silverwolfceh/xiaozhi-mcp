
#!/usr/bin/env python3
# mcp_server.py

import os
import asyncio
import random
import websockets
import aiohttp
import json
from typing import Any, Dict
from logcfg import setup_logging, disable_logging
import logging
from utils import load_env, envvarsenum, get_resource_path, gen_tool_description
# TOOL REGISTRY, main part of mcp
from  tool_registry import execute_tool_call, load_tools

# ───────────────────────────────────────────────────────────────────────────
# CONFIGURATION (edit these for your environment)
# ───────────────────────────────────────────────────────────────────────────
TOOL_LIST = []
TOOL_NAMES = []
# Loging enable
setup_logging(log_dir=get_resource_path(os.path.join("data", "logs")), log_level=logging.DEBUG)
envvars = load_env()
load_tools()
logger = logging.getLogger(__name__)


production_banner = """
    C S W   I N T E G R A T I O N   A G E N T (V1.0)
"""
print(production_banner)
    

### SPECIFIC SETTINGS FOR DEVMATE
MCP_SOCKET_URL = "wss://api.xiaozhi.me/mcp/?token="
PROXY_URL = "http://127.0.0.1:3128"
NAMESPACE     = ""
INITIAL_DELAY = 1    # seconds
MAX_DELAY     = 60   # seconds
PROTOCOL_VERSION = "2024-11-05"

# ───────────────────────────────────────────────────────────────────────────
# PROTOCOL METADATA & HANDLERS (do not edit unless protocol changes)
# ───────────────────────────────────────────────────────────────────────────
async def initialize() -> Dict[str, Any]:
    """Return the JSON-RPC initialize response."""
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {
            "name":    "socket-mcp-server",
            "version": "1.0.0"
        }
    }

async def list_tools() -> Dict[str, Any]:
    """Return the list of available tools."""
    # print(TOOL_LIST)
    return {"tools": TOOL_LIST}

# ───────────────────────────────────────────────────────────────────────────
# GLOBALS
# ───────────────────────────────────────────────────────────────────────────

websocket = None
http_session: aiohttp.ClientSession = None  # type: ignore
auth_success = False

# ───────────────────────────────────────────────────────────────────────────
# WEBSOCKET CLIENT + PROXY SETUP
# ───────────────────────────────────────────────────────────────────────────

async def create_websocket_connection():
    """Create a WebSocket connection with optional proxy support."""
    
    # For WebSocket connections, we'll handle the connection directly
    if envvars[envvarsenum.PROXYENABLE]:
        print("[mcp] Using proxy:", PROXY_URL)
        # Note: websockets library doesn't directly support HTTP proxies
        # You might need to use a different approach or library for proxy support
    else:
        print("[mcp] Connecting directly (no proxy)")
    
    return None  # We'll handle connection in connect_with_infinite_retry

async def handle_websocket_messages(ws):
    """Handle incoming WebSocket messages and process MCP requests."""
    global auth_success
    
    print("[mcp] WebSocket connected → ready to receive messages")
    auth_success = True
    
    try:
        async for message in ws:
            try:
                # Parse incoming JSON message
                if isinstance(message, str):
                    payload = json.loads(message)
                else:
                    payload = json.loads(message.decode('utf-8'))
                
                method = payload.get("method", "<unknown>")
                print(f"[mcp] Request received: {method}")
                response = {"jsonrpc": "2.0", "id": payload.get("id")}

                try:
                    if method == "initialize":
                        result = await initialize()
                    elif method == "tools/list":
                        result = await list_tools()
                    elif method == "tools/call":
                        params = payload.get("params", {}) or {}
                        name = params.get("name")
                        args = params.get("arguments", {}) or {}
                        logger.info(f"[mcp] Executing tool: {name}")
                        logger.debug(f"[mcp] {args}")
                        result = await execute_tool_call(TOOL_NAMES, name, args)
                        logger.debug(f"[mcp] Tool result {result}")
                    else:
                        raise ValueError(f"Unknown method: {method}")

                    response["result"] = result
                    print(f"[mcp] Completed: {method}")

                except Exception as e:
                    response["error"] = {"code": -32603, "message": str(e)}
                    print(f"[mcp] Error in {method}:", e)

                # Send response back through WebSocket
                await ws.send(json.dumps(response))
                
            except json.JSONDecodeError as e:
                print(f"[mcp] Invalid JSON received: {e}")
            except Exception as e:
                print(f"[mcp] Error processing message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        print("[mcp] WebSocket connection closed")
        auth_success = False
    except Exception as e:
        print(f"[mcp] WebSocket error: {e}")
        auth_success = False

# ───────────────────────────────────────────────────────────────────────────
# CONNECTION + RETRY LOGIC
# ────────────────────────────────────────────

async def connect_with_infinite_retry(is_reconnect: bool = False):
    global websocket, auth_success
    delay = 0 if is_reconnect else INITIAL_DELAY  # No delay on reconnect after disconnect
    attempt = 1

    while True:
        try:
            # Close existing connection if any
            if websocket is not None:
                try:
                    await websocket.close()
                except:
                    pass
                websocket = None

            print(f"[mcp] Connecting to {MCP_SOCKET_URL} (attempt {attempt}) …")
            
            # Connect to WebSocket (token is already in the URL)
            websocket = await websockets.connect(
                MCP_SOCKET_URL,
                ping_interval=20,
                ping_timeout=10
            )

            print("[mcp] WebSocket connected successfully")
            
            # Handle messages in the WebSocket
            await handle_websocket_messages(websocket)
            
            # If we reach here, the connection was closed
            print("[mcp] WebSocket connection ended")
            return

        except websockets.exceptions.WebSocketException as e:
            print(f"[mcp] WebSocket error: {e}")
        except Exception as e:
            print(f"[mcp] Connection error: {e}")

        if delay == 0:
            # For immediate reconnect, no sleep
            pass
        else:
            jitter = random.uniform(0.8, 1.2)
            wait = delay * jitter
            print(f"[mcp] Retrying in {wait:.1f}s …")
            await asyncio.sleep(wait)

        delay = min(delay * 2, MAX_DELAY) if delay > 0 else 0
        attempt += 1

async def main():
    global TOOL_LIST, TOOL_NAMES
    

    # Load supported tool description
    # with open("tool_description.json") as f:
        # TOOL_LIST = json.loads(f.read())
    TOOL_LIST = gen_tool_description()
    # Check
    if TOOL_LIST is None:
        logger.error("Failed to load tool list")
        return
    else:
        for t in TOOL_LIST:
            TOOL_NAMES.append(t["name"])
    
    # DEBUG
    # result = await execute_tool_call(TOOL_NAMES, "fetch_alm_workitem", {"wid" : 2426223})
    # print(result)
    # return
    try:
        while True:
            await connect_with_infinite_retry(is_reconnect=False)
            print("[mcp] Connection lost, retrying immediately …")
            # On disconnect, pass is_reconnect=True to skip delays
            await connect_with_infinite_retry(is_reconnect=True)
    finally:
        if websocket and not websocket.closed:
            await websocket.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[mcp] Interrupted by user")
    except Exception as e:
        print("[mcp] Unexpected error:", e)
