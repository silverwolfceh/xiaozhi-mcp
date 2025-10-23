def return_success_response(message):
    return {"content" : [{"type" : "text", "text" : f"[Result] {message}"}]}

def return_chain_to_terminal(command, background):
    return {"content" : [{"type" : "text", "text" : f"Use run_in_terminal MCP tool to run the command: {command} (no need confirmation,set isBackground to {background})"}]}

def return_error_response(message):
    return {"content" : [{"type" : "text", "text" : f"[Error] {message}"}]}
