import asyncio
from server import start_server
from conversation_manager import ConversationManager

async def run_conversation():
    """Run the conversation loop with the new Gemini-MCP bridge."""
    manager = ConversationManager()
    
    print("🤖 Hello! I am your Competitive Programming Assistant.")
    print("Ask me anything about Codeforces, contests, or request plots!")
    print("(Type 'exit' or 'quit' to end the conversation)\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🧠 Gemini is thinking...")
            response = await manager.process_message(user_input)
            print(f"🤖 Assistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")

async def main():
    """Gathers and runs the MCP server and the conversation manager concurrently."""
    print("--- Starting Competitive Programming Assistant ---")

    server_task = None
    try:
        # Run the server in the background
        server_task = asyncio.create_task(start_server())

        # Give the server a moment to start up before the client tries to connect
        await asyncio.sleep(2)

        # Run the main conversation loop with new manager
        await run_conversation()

    except Exception as e:
        print(f"\n🚨 A critical error occurred in the main application: {e}")
    finally:
        # This block now runs when the conversation loop ends (e.g., you type 'exit')
        if server_task:
            print("Shutting down server...")
            server_task.cancel()
            try:
                # Wait for the task to acknowledge the cancellation
                await server_task
            except asyncio.CancelledError:
                # This is the expected outcome of a clean cancellation.
                # We catch it and do nothing to keep the console clean.
                pass

        # This tiny sleep allows all background tasks and loggers to finish cleanly,
        # preventing the final traceback from appearing on the screen.
        await asyncio.sleep(0.1)
        print("Application has shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This handles Ctrl+C for a graceful shutdown.
        print("\nApplication shutting down by user request.")