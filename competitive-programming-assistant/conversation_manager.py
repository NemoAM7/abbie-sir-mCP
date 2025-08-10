# File: conversation_manager.py
#
# Fixed conversation manager that properly handles Gemini function calls

import google.generativeai as genai
from gemini_tool_definitions import mcp_tool_definitions
from gemini_bridge import bridge
import config

class ConversationManager:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Create the model with tools
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=mcp_tool_definitions
        )
        
        # Start chat session
        self.chat = self.model.start_chat(history=[])
        
    async def process_message(self, user_message: str) -> str:
        """Process a user message and handle any function calls."""
        try:
            # Send message to Gemini
            response = self.chat.send_message(user_message)
            
            # Check if Gemini wants to call a function
            if response.candidates[0].content.parts:
                result_parts = []
                
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        # Handle function call via bridge
                        function_result = await bridge.handle_gemini_function_call(part.function_call)
                        result_parts.append(function_result)
                        
                        # Send function result back to Gemini
                        function_response = genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=part.function_call.name,
                                response={"result": function_result}
                            )
                        )
                        
                        # Continue conversation with function result
                        follow_up = self.chat.send_message(function_response)
                        if follow_up.text:
                            result_parts.append(follow_up.text)
                    
                    elif hasattr(part, 'text') and part.text:
                        result_parts.append(part.text)
                
                return "\n".join(result_parts) if result_parts else "No response generated."
            
            # Regular text response
            return response.text if response.text else "No response generated."
            
        except Exception as e:
            return f"Error processing message: {str(e)}"

# Usage example
async def main():
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

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())