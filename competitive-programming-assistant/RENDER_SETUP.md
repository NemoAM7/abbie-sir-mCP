# Render Deployment Setup

## Keep-Alive Configuration

To prevent your Render service from spinning down after 15 minutes of inactivity, this application includes a built-in keep-alive mechanism.

### Setup Steps:

1. **Deploy your app to Render** and note the URL (e.g., `https://your-app-name.onrender.com`)

2. **Set the environment variable** `RENDER_HEALTH_URL` in your Render dashboard:
   ```
   RENDER_HEALTH_URL=https://your-app-name.onrender.com/health
   ```

3. **The keep-alive system will automatically:**
   - Start a background task when the server starts
   - Ping the health endpoint every 14 minutes
   - Keep your service active 24/7

### How it works:

- The `health_check` tool serves as a health endpoint
- A background task (`keep_alive()`) runs continuously
- Every 14 minutes, it makes an HTTP GET request to the health URL
- This prevents Render from detecting "inactivity" and spinning down the service

### Health Endpoint:

You can manually test the health endpoint by visiting:
```
https://your-app-name.onrender.com/health
```

This should return a response indicating the server is healthy with a timestamp.

### Logs:

Check your Render logs to see keep-alive activity:
- `✅ Keep-alive ping successful at [timestamp]` - Normal operation
- `⚠️ Keep-alive ping returned status [code]` - HTTP error but service still running
- `❌ Keep-alive ping failed: [error]` - Network or other error occurred

### Notes:

- If `RENDER_HEALTH_URL` is not set, the keep-alive task will skip and log a warning
- The service continues normally even if keep-alive pings fail
- This only affects Render's free tier - paid tiers don't have the same sleep behavior
