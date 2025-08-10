import asyncio
import json
import base64
import aiohttp
import config

# --- CHOOSE A TOOL TO TEST ---
# Change these values to test different tools and parameters
TOOL_TO_CALL = "get_codeforces_user_stats"
TOOL_PARAMETERS = {"handles": ["tourist", "Benq"]}
# Example 2:
# TOOL_TO_CALL = "plot_rating_graph"
# TOOL_PARAMETERS = {"handles": ["tourist", "Benq"]}

async def client_flow():
    # This function is for manual testing of your tools
    import os
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("AUTH_TOKEN")
    if not token:
        print("❌ AUTH_TOKEN not found in environment."); return
    await asyncio.sleep(2)
    SERVER_URL = f"http://{config.SERVER_HOST}:{config.SERVER_PORT}/mcp/"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}", "Accept": "application/json, text/event-stream"}
    init_data = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(SERVER_URL, headers=headers, json=init_data) as resp:
                if resp.status != 200:
                    print(f"❌ Error initializing session: {resp.status}"); return
                session_id = resp.headers.get("mcp-session-id")
            session_headers = {**headers, "Mcp-Session-Id": session_id}
            await session.post(SERVER_URL, headers=session_headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
            tool_call_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": TOOL_TO_CALL, "arguments": TOOL_PARAMETERS}}
            print(f"\n▶️  Calling tool '{TOOL_TO_CALL}'...")
            async with session.post(SERVER_URL, headers=session_headers, json=tool_call_payload) as resp:
                response_text = await resp.text()
                json_start = response_text.find("data: "); json_string = response_text[json_start + len("data: "):].strip() if json_start != -1 else response_text.strip()
                response_data = json.loads(json_string)
                if "error" in response_data:
                    print(f"❌ Tool call failed: {response_data['error']['message']}")
                else:
                    contents = response_data["result"]["content"]
                    image_count = 1
                    for item in contents:
                        if item.get("type") == "text":
                            print("\n" + "="*50 + "\n" + item["text"] + "\n" + "="*50 + "\n")
                        elif item.get("type") == "image":
                            image_data = base64.b64decode(item["data"])
                            output_filename = f"output_{image_count}.png"
                            with open(output_filename, "wb") as f:
                                f.write(image_data)
                            print(f"🖼️  Image content received and saved to '{output_filename}' (first 100 base64 chars: {item['data'][:100]})")
                            image_count += 1
        except Exception as e:
            print(f"❌ An unexpected error occurred in client_flow: {e}")
# Run the client flow
if __name__ == "__main__":
    asyncio.run(client_flow())