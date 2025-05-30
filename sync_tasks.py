import os
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise EnvironmentError("MONGO_URI environment variable not set")

client = MongoClient(MONGO_URI)
db = client.get_database()  # Automatically gets the DB from URI

tasks_refresh_collection = db["tasks_refresh"]
tasks_collection = db["tasks"]

# Define IST (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))
current_date = datetime.now(IST).strftime('%Y-%m-%d')
logger.info(f"Syncing tasks for date: {current_date}")

refresh_tasks = list(tasks_refresh_collection.find({}))
logger.info(f"Found {len(refresh_tasks)} tasks in tasks_refresh collection")

if not refresh_tasks:
    logger.info("No tasks to sync.")
else:
    for task in refresh_tasks:
        task_data = task.copy()
        task_data.pop("_id", None)
        task_data["date"] = current_date
        task_data["comments"] = []
        task_data["status_trail"] = []
        tasks_collection.insert_one(task_data)

    logger.info("Sync completed successfully.")
