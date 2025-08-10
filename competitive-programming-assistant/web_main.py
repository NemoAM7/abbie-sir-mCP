import os
import asyncio
from server import start_server
import config

# Use PORT from environment if available (Render sets this)
config.SERVER_PORT = int(os.environ.get("PORT", config.SERVER_PORT))

async def main():
    print(f"--- Starting Competitive Programming Assistant Web Server on port {config.SERVER_PORT} ---")
    await start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication shutting down by user request.")
