import logging
import threading
import time
from database.models import User, get_session

logger = logging.getLogger(__name__)

class DatabaseMonitor:
    """Monitors database changes and synchronizes worker_manager accordingly."""
    
    def __init__(self, worker_manager_instance, poll_interval=5):
        """Initialize the monitor with a worker_manager instance.
        
        Args:
            worker_manager_instance: Instance of worker_manager from worker.py
            poll_interval: How often to check the database (in seconds)
        """
        self.worker_manager = worker_manager_instance
        self.poll_interval = poll_interval
        self.running = False
        self._thread = None
        self._known_users = {}  # user_id -> {url, enabled, premium}
        
    def start(self):
        """Start monitoring database changes."""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            logger.info(f"Database monitor started - polling every {self.poll_interval}s")
    
    def stop(self):
        """Stop monitoring database changes."""
        if self.running:
            self.running = False
            if self._thread:
                self._thread.join(timeout=self.poll_interval + 1)
            logger.info("Database monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop that polls the database."""
        while self.running:
            try:
                self._check_for_changes()
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.poll_interval * 10):
                if not self.running:
                    break
                time.sleep(0.1)
    
    def _check_for_changes(self):
        """Check database for user changes and sync workers."""
        session = get_session()
        try:
            # Get all users from database
            all_users = session.query(User).all()
            current_user_ids = set()
            
            for user in all_users:
                user_id = str(user.user_id)
                current_user_ids.add(user_id)
                
                user_info = {
                    'url': user.user_url,
                    'enabled': user.user_enable,
                    'premium': user.is_premium,
                    'email': user.user_email
                }
                
                if user_id not in self._known_users:
                    # New user detected
                    self._known_users[user_id] = user_info
                    self._handle_new_user(user_id, user_info)
                else:
                    # Check if existing user changed
                    old_info = self._known_users[user_id]
                    if old_info != user_info:
                        self._known_users[user_id] = user_info
                        self._handle_user_update(user_id, old_info, user_info)
            
            # Check for deleted users
            known_user_ids = set(self._known_users.keys())
            deleted_user_ids = known_user_ids - current_user_ids
            for user_id in deleted_user_ids:
                self._handle_user_delete(user_id, self._known_users[user_id])
                del self._known_users[user_id]
                
        finally:
            session.close()
    
    def _handle_new_user(self, user_id, user_info):
        """Handle a newly detected user."""
        if user_info['enabled']:
            logger.info(f"New user detected (ID: {user_id}). Starting worker...")
            self.worker_manager.add_worker(user_id, user_info['url'])
            logger.info(f"Worker started for user {user_id}")
        else:
            logger.info(f"New user detected (ID: {user_id}) but disabled. Skipping worker creation.")
    
    def _handle_user_update(self, user_id, old_info, new_info):
        """Handle changes to an existing user."""
        is_worker_running = self.worker_manager.is_worker_running(user_id)
        
        # Check if enabled status changed
        if old_info['enabled'] != new_info['enabled']:
            if new_info['enabled']:
                # User was enabled
                if not is_worker_running:
                    logger.info(f"User {user_id} enabled. Starting worker...")
                    self.worker_manager.add_worker(user_id, new_info['url'])
                    logger.info(f"Worker started for user {user_id}")
            else:
                # User was disabled
                if is_worker_running:
                    logger.info(f"User {user_id} disabled. Stopping worker...")
                    self.worker_manager.remove_worker(user_id)
                    logger.info(f"Worker stopped for user {user_id}")
        
        # Check if URL changed
        elif old_info['url'] != new_info['url'] and new_info['enabled']:
            # URL changed for an enabled user - restart worker
            logger.info(f"URL changed for user {user_id}. Restarting worker...")
            if is_worker_running:
                self.worker_manager.remove_worker(user_id)
            self.worker_manager.add_worker(user_id, new_info['url'])
            logger.info(f"Worker restarted for user {user_id} with new URL")
        
        # Check if premium status changed
        if old_info['premium'] != new_info['premium']:
            logger.info(f"Premium status changed for user {user_id}: {old_info['premium']} -> {new_info['premium']}")
    
    def _handle_user_delete(self, user_id, user_info):
        """Handle a deleted user."""
        if self.worker_manager.is_worker_running(user_id):
            logger.info(f"User {user_id} deleted. Stopping worker...")
            self.worker_manager.remove_worker(user_id)
            logger.info(f"Worker stopped for deleted user {user_id}")
        else:
            logger.info(f"User {user_id} deleted but no worker was running.")


def monitor(worker_manager_instance, poll_interval=5):
    """Create and start a database monitor for the given worker_manager.
    
    Args:
        worker_manager_instance: Instance of worker_manager from worker.py
        poll_interval: How often to check for changes (in seconds, default=5)
        
    Returns:
        DatabaseMonitor instance
    """
    mon = DatabaseMonitor(worker_manager_instance, poll_interval)
    mon.start()
    return mon
