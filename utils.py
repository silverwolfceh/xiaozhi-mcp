from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
import base64
import sys
import ast
import json

class envvarsenum:
    MCP_JWT = "MCP_JWT"
    PROXYENABLE = "PROXYENABLE"
    CMC_API_KEY = "COIN_MARKETCAP_API_KEY"

def get_resource_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as a regular Python script
        base_path = os.path.dirname(os.path.abspath(__file__))


    return os.path.join(base_path, relative_path)

def get_static_file(filename):
    static_path = os.path.join("data", "static", filename)
    fullpath = get_resource_path(static_path)
    return fullpath

def get_runtime_path(foldername = None):
    runtime_path = os.path.join("data", "runtime")
    fullpath = get_resource_path(runtime_path)
    os.makedirs(fullpath, exist_ok=True)
    if foldername:
        fullpath = os.path.join(fullpath, foldername)
        os.makedirs(fullpath, exist_ok=True)
    return fullpath

def get_log_folder():
    log_path = os.path.join("data", "logs")
    fullpath = get_resource_path(log_path)
    os.makedirs(fullpath, exist_ok=True)
    return fullpath

def encrypt_password(password: str, key: str) -> str:
    key = base64.urlsafe_b64encode(key.ljust(32)[:32].encode())
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()

def decrypt_password(token: str, key: str) -> str:
    key = base64.urlsafe_b64encode(key.ljust(32)[:32].encode())
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()

def get_password_hash(plainpass):
    secretfile = get_resource_path(".secrect")
    if os.path.isfile(secretfile):
        with open(secretfile, "r") as f:
            secretkey = f.read().strip()
            try:
                encpass = encrypt_password(plainpass, secretkey)
                return encpass
            except Exception as e:
                print("Failed to encrypt password")
                print(e)
                sys.exit(3)
    else:
        print("Create the .secrect file with key")
        sys.exit(2)

def get_password(encpass):
    secretfile = get_resource_path(".secrect")
    if os.path.isfile(secretfile):
        with open(secretfile, "r") as f:
            secretkey = f.read().strip()
            try:
                decpass = decrypt_password(encpass, secretkey)
                return decpass
            except Exception as e:
                print("Failed to descrypt password")
                print(e)
                sys.exit(3)
    else:
        print("Create the .secrect file with any text string")
        sys.exit(2)

def load_env():
    envpath = get_resource_path(".env")
    if os.path.isfile(envpath):
        load_dotenv(get_resource_path(".env"))
    else:
        print("Failed to load .env")
        sys.exit(1)
    envvars = {
        envvarsenum.MCP_JWT            : os.getenv("MCP_JWT", ""),
        envvarsenum.PROXYENABLE        : os.getenv("PROXYENABLE", "false").lower() == "true",
        envvarsenum.CMC_API_KEY        : os.getenv("COIN_MARKETCAP_API_KEY", "")
    }
    return envvars

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
                                print(f"Warning: Could not parse JSON in docstring of {node.name} in {filename}")
    return tools

if __name__ == "__main__":
    yourpass = input("Your plain password (will be stripped): ")
    yourpass = yourpass.strip()
    print(f"3 Characters: ***{yourpass[2:5]}***")
    encpass = get_password_hash(yourpass)
    print(f"OK, copy and paste below encrypted password to the NT_PASSWORD in .env")
    print(f"NT_PASSWORD=\"{encpass}\"")
    decpass = get_password(encpass)
    if decpass == yourpass:
        print("PASS")
    else:
        print("FAILED")
