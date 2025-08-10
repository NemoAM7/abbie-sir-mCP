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

async def start_server():
    """Starts the MCP server."""
    print(f"🚀 Starting server on http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    # The mcp object is now imported from our central instance file
    await mcp.run_async("streamable-http", host=config.SERVER_HOST, port=config.SERVER_PORT)