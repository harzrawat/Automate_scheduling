from pymongo import MongoClient
from datetime import datetime
import logging
import os

# Configuration
MONGO_URI = os.getenv("MONGO_URI") or "your_mongodb_atlas_uri"
DB_NAME = "task_management_system"
REFRESH_COLLECTION = "tasks_refresh"
TASKS_COLLECTION = "tasks"

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_tasks():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    refresh_col = db[REFRESH_COLLECTION]
    tasks_col = db[TASKS_COLLECTION]

    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    logger.info(f"Syncing tasks for date: {current_date}")

    refresh_tasks = list(refresh_col.find())
    logger.info(f"Found {len(refresh_tasks)} tasks in {REFRESH_COLLECTION}")

    if not refresh_tasks:
        logger.info("No tasks to sync.")
        return

    for task in refresh_tasks:
        task_data = task.copy()
        task_data.pop('_id', None)  # Remove MongoDB ID
        task_data['date'] = current_date
        task_data['comments'] = []
        task_data['status_trail'] = []

        try:
            tasks_col.insert_one(task_data)
        except Exception as e:
            logger.error(f"Failed to insert task: {e}")

    logger.info("Task syncing completed.")

if __name__ == "__main__":
    sync_tasks()
