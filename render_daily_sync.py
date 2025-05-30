#!/usr/bin/env python3
"""
Render Daily Task Sync Script
Single file for deploying on Render.com with automatic scheduling
Syncs tasks from tasks_refresh to tasks collection daily at 00:02 AM
"""

import os
import sys
from datetime import datetime
import logging
from pymongo import MongoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Render captures stdout
    ]
)

logger = logging.getLogger(__name__)

class TaskSyncService:
    def __init__(self):
        """Initialize with MongoDB connection"""
        self.mongo_uri = os.getenv('MONGO_URI')
        if not self.mongo_uri:
            raise ValueError("MONGO_URI environment variable is required")
        
        self.client = MongoClient(self.mongo_uri)
        # Extract database name from URI or use default
        self.db_name = self.mongo_uri.split('/')[-1].split('?')[0] if '/' in self.mongo_uri else 'task_management'
        self.db = self.client[self.db_name]
        
        logger.info(f"Connected to database: {self.db_name}")
    
    def test_connection(self):
        """Test database connection and collections"""
        try:
            tasks_refresh_collection = self.db['tasks_refresh']
            tasks_collection = self.db['tasks']
            
            # Test connection
            refresh_count = tasks_refresh_collection.count_documents({})
            tasks_count = tasks_collection.count_documents({})
            
            logger.info(f"Database connection successful!")
            logger.info(f"tasks_refresh collection: {refresh_count} documents")
            logger.info(f"tasks collection: {tasks_count} documents")
            
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
    
    def sync_tasks_daily(self):
        """
        Main function to sync tasks from tasks_refresh to tasks collection
        """
        try:
            logger.info("Starting daily task sync process...")
            
            tasks_refresh_collection = self.db['tasks_refresh']
            tasks_collection = self.db['tasks']
            
            # Get current date
            current_date = datetime.now().strftime('%Y-%m-%d')
            logger.info(f"Syncing tasks for date: {current_date}")
            
            # Fetch all documents from tasks_refresh
            refresh_tasks = list(tasks_refresh_collection.find({}))
            logger.info(f"Found {len(refresh_tasks)} tasks in tasks_refresh collection")
            
            if not refresh_tasks:
                logger.info("No tasks found in tasks_refresh collection. Nothing to sync.")
                return True
            
            synced_count = 0
            failed_count = 0
            
            for task in refresh_tasks:
                try:
                    # Prepare task data for tasks collection
                    task_data = task.copy()
                    
                    # Remove MongoDB _id to let it generate a new one
                    if '_id' in task_data:
                        del task_data['_id']
                    
                    # Add required attributes for tasks collection
                    task_data['date'] = current_date
                    task_data['comments'] = []
                    task_data['status_trail'] = []
                    
                    # Insert into tasks collection
                    result = tasks_collection.insert_one(task_data)
                    
                    if result.inserted_id:
                        synced_count += 1
                        logger.info(f"Successfully synced task: {task_data.get('title', 'Unknown')} (ID: {result.inserted_id})")
                    else:
                        failed_count += 1
                        logger.error(f"Failed to insert task: {task_data.get('title', 'Unknown')}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error syncing task {task.get('title', 'Unknown')}: {str(e)}")
            
            # Log summary
            logger.info(f"Daily sync completed. Synced: {synced_count}, Failed: {failed_count}")
            
            # Optional: Clear tasks_refresh collection after successful sync
            # Uncomment the following lines if you want to clear tasks_refresh after sync
            # if synced_count > 0 and failed_count == 0:
            #     tasks_refresh_collection.delete_many({})
            #     logger.info("Cleared tasks_refresh collection after successful sync")
            
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"Critical error in daily sync process: {str(e)}")
            return False
        finally:
            # Close database connection
            self.client.close()
    
    def get_sync_status(self):
        """
        Get current sync status and statistics
        """
        try:
            tasks_refresh_collection = self.db['tasks_refresh']
            tasks_collection = self.db['tasks']
            
            # Get current date and yesterday
            today = datetime.now().strftime('%Y-%m-%d')
            
            logger.info("=== Daily Task Sync Status ===")
            logger.info(f"Current date: {today}")
            
            # Check tasks_refresh collection
            refresh_count = tasks_refresh_collection.count_documents({})
            logger.info(f"📋 Tasks in tasks_refresh: {refresh_count}")
            
            # Check today's tasks
            today_tasks = tasks_collection.count_documents({"date": today})
            logger.info(f"📅 Tasks for today ({today}): {today_tasks}")
            
            # Check recent tasks (last 7 days)
            from datetime import timedelta
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            recent_tasks = tasks_collection.count_documents({
                "date": {"$gte": seven_days_ago}
            })
            logger.info(f"📊 Tasks in last 7 days: {recent_tasks}")
            
            # Get unique dates from tasks collection (last 10 days)
            pipeline = [
                {"$match": {"date": {"$exists": True}}},
                {"$group": {"_id": "$date", "count": {"$sum": 1}}},
                {"$sort": {"_id": -1}},
                {"$limit": 10}
            ]
            
            recent_dates = list(tasks_collection.aggregate(pipeline))
            
            if recent_dates:
                logger.info("=== Recent Task Dates ===")
                for date_info in recent_dates:
                    date_str = date_info["_id"]
                    count = date_info["count"]
                    logger.info(f"  {date_str}: {count} tasks")
            
            # Check if sync might be needed
            if refresh_count > 0 and today_tasks == 0:
                logger.warning("⚠️  WARNING: tasks_refresh has data but no tasks for today!")
                logger.warning("   The daily sync might not have run yet or failed.")
            elif refresh_count > 0 and today_tasks > 0:
                logger.info("✅ Tasks exist for today. Sync appears to be working.")
            elif refresh_count == 0:
                logger.info("ℹ️  No tasks in tasks_refresh collection.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking sync status: {str(e)}")
            return False
        finally:
            # Close database connection
            self.client.close()

def main():
    """
    Main entry point - handles different modes based on command line arguments
    """
    try:
        # Initialize service
        sync_service = TaskSyncService()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "--test":
                logger.info("Running in test mode...")
                success = sync_service.test_connection()
                if success:
                    logger.info("Test completed successfully!")
                    sys.exit(0)
                else:
                    logger.error("Test failed!")
                    sys.exit(1)
            
            elif command == "--status":
                logger.info("Checking sync status...")
                success = sync_service.get_sync_status()
                sys.exit(0 if success else 1)
            
            elif command == "--help":
                print("Usage:")
                print("  python render_daily_sync.py           # Run daily sync")
                print("  python render_daily_sync.py --test    # Test database connection")
                print("  python render_daily_sync.py --status  # Check sync status")
                print("  python render_daily_sync.py --help    # Show this help")
                sys.exit(0)
        
        # Default: Run the daily sync
        logger.info("Running daily task synchronization...")
        success = sync_service.sync_tasks_daily()
        
        if success:
            logger.info("Daily sync completed successfully!")
            sys.exit(0)
        else:
            logger.error("Daily sync completed with errors!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
