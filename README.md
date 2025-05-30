# Render Daily Task Sync Deployment

This directory contains everything needed to deploy the daily task sync script on Render.com with automatic scheduling.

## Files for Deployment

1. **`render_daily_sync.py`** - Main script (single file, no dependencies on other project files)
2. **`requirements.txt`** - Python dependencies
3. **`render.yaml`** - Render configuration for cron job
4. **`README_RENDER.md`** - This deployment guide

## Deployment Steps

### 1. Create GitHub Repository
```bash
# Create a new repository or use existing one
# Upload these 4 files to GitHub:
# - render_daily_sync.py
# - requirements.txt  
# - render.yaml
# - README_RENDER.md
```

### 2. Deploy on Render
1. Go to [render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Select the repository containing these files
6. Render will automatically detect `render.yaml`

### 3. Set Environment Variables
In Render dashboard:
1. Go to your deployed service
2. Click "Environment"
3. Add environment variable:
   - **Key**: `MONGO_URI`
   - **Value**: Your MongoDB Atlas connection string
   - Example: `mongodb+srv://username:password@cluster.mongodb.net/database_name`

### 4. Verify Deployment
- Check "Logs" tab in Render dashboard
- Should show successful deployment
- Cron job will run daily at 00:02 AM UTC

## Manual Testing

You can trigger the script manually in Render:

### Test Database Connection
```bash
python render_daily_sync.py --test
```

### Check Sync Status
```bash
python render_daily_sync.py --status
```

### Run Sync Manually
```bash
python render_daily_sync.py
```

## Monitoring

### Render Dashboard
- **Logs**: View execution logs
- **Metrics**: Monitor performance
- **Events**: See deployment history

### Log Output
The script logs:
- Connection status
- Tasks found in tasks_refresh
- Sync progress
- Success/failure counts
- Error details

## Pricing

**Render Cron Jobs:**
- Free tier: 750 hours/month
- Paid: $7/month for unlimited
- Your script runs ~1 minute daily = ~30 minutes/month (well within free tier)

## Troubleshooting

### Common Issues

1. **"MONGO_URI not found"**
   - Set MONGO_URI environment variable in Render dashboard

2. **"Database connection failed"**
   - Check MongoDB Atlas connection string
   - Verify database name in connection string
   - Check MongoDB Atlas IP whitelist (allow 0.0.0.0/0 for Render)

3. **"No tasks in tasks_refresh"**
   - Normal if no tasks to sync
   - Check your main application is adding tasks to tasks_refresh

### Debug Commands
```bash
# Test connection
python render_daily_sync.py --test

# Check status
python render_daily_sync.py --status

# View help
python render_daily_sync.py --help
```

## How It Works

1. **Daily Schedule**: Runs at 00:02 AM UTC every day
2. **Data Sync**: Copies all documents from `tasks_refresh` to `tasks` collection
3. **Data Enhancement**: Adds current date, empty comments[], empty status_trail[]
4. **Logging**: All operations logged to Render console
5. **Error Handling**: Continues on errors, reports status

## File Structure for GitHub

```
your-repo/
├── render_daily_sync.py    # Main script
├── requirements.txt        # Dependencies
├── render.yaml            # Render configuration
└── README_RENDER.md       # This guide
```

## Success Indicators

✅ **Deployment Successful**: No errors in Render logs
✅ **Database Connected**: Test command shows connection success
✅ **Cron Scheduled**: Render shows next execution time
✅ **Tasks Syncing**: Daily logs show tasks being copied
✅ **Data Updated**: MongoDB Atlas shows new tasks with current date

## Next Steps After Deployment

1. **Monitor First Run**: Check logs after 00:02 AM UTC
2. **Verify Data**: Check MongoDB Atlas for new tasks with current date
3. **Set Alerts**: Configure Render notifications for failures
4. **Test Manually**: Run test commands to verify everything works

Your daily task sync will now run automatically 24/7, even when your computer is off!
