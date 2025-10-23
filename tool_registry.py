import os
import subprocess
import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Any, Dict, List
from utils import get_resource_path
import logging

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
