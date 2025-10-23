import requests
from typing import Any, Dict, List

def get_my_ipaddress_info_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    {
        "name": "get_my_ipaddress_info",
        "description": "",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description" : "The IP address to lookup. Use blank to lookup your own IP address."
                }
            },
            "required": ["query"]
        }
    }
    """
    url = "http://ip-api.com/json/"
    res = requests.get(url)
    return {"content" : [{"type" : "text", "text" : f"[Result] {res.json()}"}]}
