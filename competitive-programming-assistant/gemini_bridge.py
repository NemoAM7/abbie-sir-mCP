# File: gemini_mcp_bridge.py
#
# This file handles the conversion between Gemini's function calling format
# and MCP tool calling format.

import json
import asyncio
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from mcp_instance import mcp

class GeminiMCPBridge:
    """Bridges Gemini function calls to MCP tool calls."""
    
    def __init__(self):
        self.mcp_client = mcp
    
    def convert_gemini_to_mcp_call(self, function_call) -> Dict[str, Any]:
        """Convert Gemini function call to MCP format."""
        try:
            # Extract function name and arguments from Gemini's function call
            function_name = function_call.name
            
            # Parse arguments - Gemini may send them in different formats
            if hasattr(function_call, 'args') and function_call.args:
                # Convert Gemini's args to a regular dict
                args = {}
                for key, value in function_call.args.items():
                    args[key] = value
            else:
                args = {}
            
            return {
                "method": "tools/call",
                "params": {
                    "name": function_name,
                    "arguments": args
                }
            }
        except Exception as e:
            print(f"Error converting Gemini function call: {e}")
            return None
    
    async def handle_gemini_function_call(self, function_call) -> str:
        """Handle a function call from Gemini and execute it via MCP."""
        try:
            # Convert Gemini function call to MCP format
            mcp_call = self.convert_gemini_to_mcp_call(function_call)
            if not mcp_call:
                return "Error: Could not convert function call"
            
            # Extract function name and arguments
            function_name = mcp_call["params"]["name"]
            arguments = mcp_call["params"]["arguments"]
            
            # Call the MCP tool directly
            result = await self.call_mcp_tool(function_name, arguments)
            return result
            
        except Exception as e:
            return f"Error executing function call: {str(e)}"
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool with the given arguments."""
        try:
            # Use the tool manager's call_tool method
            tool_result = await self.mcp_client._tool_manager.call_tool(tool_name, arguments)
            
            # Extract the actual result from the ToolResult object
            if hasattr(tool_result, 'content'):
                # Handle different content types
                if isinstance(tool_result.content, list):
                    # Handle multiple content parts (text and images)
                    text_parts = []
                    image_count = 0
                    
                    for content_part in tool_result.content:
                        if hasattr(content_part, 'type') and content_part.type == 'text':
                            text_parts.append(content_part.text)
                        elif hasattr(content_part, 'type') and content_part.type == 'image':
                            image_count += 1
                    
                    response = "\n".join(text_parts) if text_parts else ""
                    if image_count > 0:
                        response += f"\n[Image generated: {image_count} chart(s)]"
                    
                    return response if response else "No content returned"
                    
                elif hasattr(tool_result.content, 'text'):
                    # Single text content
                    return tool_result.content.text
                else:
                    # Fallback to string representation
                    return str(tool_result.content)
            
            elif hasattr(tool_result, 'result'):
                # Alternative: result might be in a 'result' attribute
                return str(tool_result.result)
            else:
                # Fallback: convert the whole object to string
                return str(tool_result)
                
        except Exception as e:
            return f"Error calling MCP tool {tool_name}: {str(e)}"

# Global bridge instance
bridge = GeminiMCPBridge()