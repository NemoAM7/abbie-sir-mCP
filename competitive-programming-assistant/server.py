import asyncio
import aiohttp
from datetime import datetime
import config
from mcp_instance import mcp

# IMPORTANT: By importing these modules, you are causing the @mcp.tool decorators
# inside them to run, which registers the tools with the `mcp` object.
import tools.codeforces_tools
import tools.contest_tools
import tools.graphing_tools
import tools.leetcode_tools

# The validation tool can be defined here directly
@mcp.tool
async def validate() -> str:
    return config.MY_NUMBER

# Health check endpoint to keep Render server alive
@mcp.tool
async def health_check() -> str:
    """Health check endpoint to prevent Render server from sleeping."""
    return f"Server is healthy at {datetime.now().isoformat()}"

async def keep_alive():
    """Background task that pings the health endpoint every 5 minutes to keep Render server alive."""
    if not hasattr(config, 'RENDER_HEALTH_URL') or not config.RENDER_HEALTH_URL:
        print("⚠️  RENDER_HEALTH_URL not configured, skipping keep-alive pings")
        return
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await asyncio.sleep(5 * 60)  # Wait 5 minutes
                async with session.get(config.RENDER_HEALTH_URL, timeout=30) as response:
                    if response.status == 200:
                        print(f"✅ Keep-alive ping successful at {datetime.now().isoformat()}")
                    else:
                        print(f"⚠️  Keep-alive ping returned status {response.status}")
            except Exception as e:
                print(f"❌ Keep-alive ping failed: {e}")
                # Continue the loop even if one ping fails

async def start_server():
    """Starts the MCP server and background keep-alive task."""
    print(f"🚀 Starting server on http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    
    # Start the keep-alive task in the background
    asyncio.create_task(keep_alive())
    print("🔄 Started keep-alive background task")
    
    # The mcp object is now imported from our central instance file
    await mcp.run_async("streamable-http", host=config.SERVER_HOST, port=config.SERVER_PORT)