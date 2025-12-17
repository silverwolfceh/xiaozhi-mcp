from worker import worker_manager
from logcfg import setup_logging
from database.models import User, get_session
from monitor import monitor
from tool_manager import tool_functions

logger = setup_logging(__name__)


if __name__ == "__main__":
    tools = tool_functions()
    tools.load_tools()
    wm = worker_manager(tools)
    
    # Start database monitor to automatically manage workers
    db_monitor = monitor(wm)
    logger.info("Database monitor started - workers will be automatically managed")
   
    # Register worker for all users in the database
    session = get_session()
    active_users = session.query(User).filter(User.user_enable == True).all()
    for user in active_users:
        url = user.user_url
        wm.add_worker(user.user_id, url)
        logger.info(f"Started worker for user {user.user_id} with URL {url}")
    session.close()
    
    try:
        while True:
            # Keep the main thread alive to maintain workers
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        db_monitor.stop()
        logger.info("Stopping all workers...")
        wm.stop_all_workers()
        logger.info("Shutdown complete")
