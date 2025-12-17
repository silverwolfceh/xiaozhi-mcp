import os
import subprocess
import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Any, Dict, List
from utils import get_resource_path
import logging
import ast
import json

logger = logging.getLogger("ToolRegistry")

tool_functions = {}

def load_tools():
    # Dynamically import all modules in the 'tools' directory and collect *_tool functions
    TOOLS_DIR = get_resource_path("tools")
    PLUGINS_DIR = get_resource_path("plugins")


    logger.info(f"Start finding function from {TOOLS_DIR} and {PLUGINS_DIR}")

    for module_info in pkgutil.iter_modules([str(TOOLS_DIR)]):
        module_name = module_info.name
        module = importlib.import_module(f"tools.{module_name}")
        for attr in dir(module):
            if attr.endswith("_tool"):
                tool_functions[attr] = getattr(module, attr)
                logger.info(f"Found: {attr} in the {module_name}")

    for module_info in pkgutil.iter_modules([str(PLUGINS_DIR)]):
        module_name = module_info.name
        try:
            module = importlib.import_module(f"plugins.{module_name}")
        except:
            module = importlib.import_module(f"{module_name}")

        for attr in dir(module):
            if attr.endswith("_tool"):
                tool_functions[attr] = getattr(module, attr)
                logger.info(f"Found: {attr} in the {module_name}")

def get_caller(tool_names, name):
    func_name = f"{name}_tool"
    if name in tool_names and func_name in tool_functions:
        return tool_functions[func_name]
    return None

async def execute_tool_call(tool_names : List, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    caller = get_caller(tool_names, name)
    if caller is None:
        raise ValueError(f"Unknown tool: {name}")
    else:
        return caller(arguments)

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
                if isinstance(node, ast.FunctionDef):
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