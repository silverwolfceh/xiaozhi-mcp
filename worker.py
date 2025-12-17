from database.models import UserManager, ToolManager, ConnectionManager
from xiaozhi.xiaozhiconn import xiaozhiconn
import asyncio
from tool_manager import tool_functions
class worker(xiaozhiconn):
    def __init__(self, url: str, user_id: str, tools: tool_functions):
        self.url = url
        self.user_id = user_id
        self.user = UserManager.get_by_id(user_id)
        self.tools = tools
        super().__init__(url, True)

    async def mcp_proto_call_tool(self, name: str, arguments: dict):
        """Execute a tool call and return the result."""
        tool = ToolManager.get_by_name(name)
        if not tool:
            return {"status": "error", "message": f"Tool '{name}' not found."}
        if tool.tool_enable is False:
            return {"status": "error", "message": f"Tool '{name}' is disabled."}
        if self.user.is_premium:
            # Execute any tool
            return await self.tools.execute_tool_call(name, arguments)
        elif not tool.is_premium:
            # Execute non-premium tool
            return await self.tools.execute_tool_call(name, arguments)
        else:
            return {"status": "error", "message": f"Tool '{name}' is premium. Please upgrade to access."}
    
    def stop(self):
        self.close_request = True

class worker_manager:
    def __init__(self, tools):
        # Format: user_id : worker_instance
        self.workers = {}
        self.tools = tools
    
    def add_worker(self, user_id: str, url: str) -> worker:
        if user_id not in self.workers:
            self.workers[user_id] = worker(url, user_id, self.tools)
            self.workers[user_id].start()
        return self.workers[user_id]

    def remove_worker(self, user_id: str):
        if user_id in self.workers:
            worker_instance = self.workers[user_id]
            worker_instance.stop()
            asyncio.run(worker_instance.reset())
            del self.workers[user_id]

    def get_worker(self, user_id: str) -> worker:
        return self.workers.get(user_id, None)
    
    def stop_all_workers(self):
        for user_id in list(self.workers.keys()):
            self.remove_worker(user_id)

    def get_all_workers(self):
        return self.workers
    
    def is_worker_running(self, user_id: str) -> bool:
        return user_id in self.workers