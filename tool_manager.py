import os
import subprocess
import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Any, Dict, List
import importlib.metadata
import inspect
from utils import get_resource_path
import logging
import ast
import json

logger = logging.getLogger("ToolRegistry")

class tool_functions:
    def __init__(self):
        self.tool_functions = {}
    
    def load_tools(self):
        # Dynamically import all modules in the 'tools' directory and collect *_tool functions
        TOOLS_DIR = get_resource_path("tools")
        logger.info(f"Start finding function from {TOOLS_DIR}")

        for module_info in pkgutil.iter_modules([str(TOOLS_DIR)]):
            module_name = module_info.name
            module = importlib.import_module(f"tools.{module_name}")
            for attr in dir(module):
                if attr.endswith("_tool"):
                    self.tool_functions[attr] = getattr(module, attr)
                    logger.info(f"Found: {attr} in the {module_name}")

        return self.tool_functions

    def get_caller(self, name):
        func_name = f"{name}_tool"
        if func_name in self.tool_functions:
            return self.tool_functions[func_name]
        return None

    async def execute_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        caller = self.get_caller(name)
        if caller is None:
            raise ValueError(f"Unknown tool: {name}")
        else:
            if inspect.iscoroutinefunction(caller):
                return await caller(arguments)

            result = caller(arguments)

            # In case a sync wrapper returns a coroutine for some reason
            if inspect.isawaitable(result):
                return await result
    
def gen_tool_description():
    tools = []
    tools_dir = get_resource_path("tools")
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(tools_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            tree = ast.parse(file_content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.endswith('_tool'):
                        docstring = ast.get_docstring(node)
                        if docstring:
                            try:
                                tool_info = json.loads(docstring)
                                tools.append(tool_info)
                            except json.JSONDecodeError:
                                logger.warning(f"Warning: Could not parse JSON in docstring of {node.name} in {filename}")
    return tools

def get_tool_names():
    tools = gen_tool_description()
    return [tool['name'] for tool in tools]