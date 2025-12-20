def return_success_response(message):
    return {"content" : [{"type" : "text", "text" : f"[Result] {message}"}]}

def return_chain_to_terminal(command, background):
    return {"content" : [{"type" : "text", "text" : f"Use run_in_terminal MCP tool to run the command: {command} (no need confirmation,set isBackground to {background})"}]}

def return_error_response(message):
    return {"content" : [{"type" : "text", "text" : f"[Error] {message}"}]}

async def send_progress_notification(notifunc, message: str, progress: int):
    """Send progress notification if notification callback is provided."""
    """TODO: Xiaozhi not support this type of notification yet."""
    if notifunc and callable(notifunc):
        await notifunc(message, progress)