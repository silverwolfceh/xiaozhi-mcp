from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
import base64
import sys


class envvarsenum:
    CMC_API_KEY = "CMC_API_KEY"
    GEMINI_API_KEY = "GEMINI_API_KEY"
    OPENAI_API_KEY= "OPENAI_API_KEY"
    KEY_FILE    = "mcpsecrect.key"
    ADMIN_USER  = "ADMIN_USER"
    ADMIN_PASSWORD = "ADMIN_PASSWORD"

def get_resource_path(relative_path: str) -> str:
    # Give you a final path from the prog direct rootory
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as a regular Python script
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def get_key_file():
    """Get the path to the key file in user's home directory"""
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".xiaozhi-mcp")
    os.makedirs(key_dir, exist_ok=True)
    key_file = os.path.join(key_dir, envvarsenum.KEY_FILE)
    return key_file

def get_persistent_data(filename):
    # Get a persistent data file path
    persistent_path = os.path.join("data", "persistent", filename)
    fullpath = get_resource_path(persistent_path)
    return fullpath

def get_log_path(filename):
    log_path = os.path.join("data", "logs", filename)
    fullpath = get_resource_path(log_path)
    os.makedirs(os.path.dirname(fullpath), exist_ok=True)
    return fullpath

def get_log_dir():
    log_dir = os.path.join("data", "logs")
    fullpath = get_resource_path(log_dir)
    os.makedirs(fullpath, exist_ok=True)
    return fullpath

def get_runtime_path(foldername = None):
    runtime_path = os.path.join("data", "runtime")
    fullpath = get_resource_path(runtime_path)
    os.makedirs(fullpath, exist_ok=True)
    if foldername:
        fullpath = os.path.join(fullpath, foldername)
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
    secretfile = get_key_file()
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
    secretfile = get_key_file()
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

    keyfile = get_key_file()
    if not os.path.isfile(keyfile):
        # create a key file
        with open(keyfile, "w") as f:
            f.write(base64.urlsafe_b64encode(Fernet.generate_key()).decode())
            print("Key file generated. Please tell me your password")
            yourpass = input("Your plain password (will be stripped): ").strip()
            encpass = get_password_hash(yourpass)
            print(f"OK, copy and paste below encrypted password to the ADMIN_PASSWORD in .env")
            print(f"ADMIN_PASSWORD=\"{encpass}\"")
            print("Then restart the server")
            sys.exit(0)
    else:
        decpass = get_password(os.getenv(envvarsenum.ADMIN_PASSWORD, ""))
    envvars = {
        envvarsenum.ADMIN_USER         : os.getenv(envvarsenum.ADMIN_USER, "admin"),
        envvarsenum.ADMIN_PASSWORD     : decpass,
        envvarsenum.CMC_API_KEY        : os.getenv(envvarsenum.CMC_API_KEY, ""),
        envvarsenum.GEMINI_API_KEY     : os.getenv(envvarsenum.GEMINI_API_KEY, ""),
        envvarsenum.OPENAI_API_KEY     : os.getenv(envvarsenum.OPENAI_API_KEY, "")
    }
    return envvars

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
