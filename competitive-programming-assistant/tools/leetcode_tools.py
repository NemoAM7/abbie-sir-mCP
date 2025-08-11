import re

def format_for_whatsapp(html: str) -> str:
    """
    Convert LeetCode HTML content to WhatsApp-friendly plain text.
    - Remove HTML tags
    - Replace <strong>, <b> with *bold*
    - Replace <em>, <i> with _italics_
    - Preserve code/pre blocks as monospace
    """
    text = html
    # Replace bold tags
    text = re.sub(r'<(strong|b)>(.*?)</\1>', r'*\2*', text, flags=re.DOTALL)
    # Replace italics tags
    text = re.sub(r'<(em|i)>(.*?)</\1>', r'_\2_', text, flags=re.DOTALL)
    # Replace code/pre tags with backticks
    text = re.sub(r'<pre>(.*?)</pre>', lambda m: '```\n' + m.group(1).strip() + '\n```', text, flags=re.DOTALL)
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities
    import html as html_module
    text = html_module.unescape(text)
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
from mcp import ErrorData, McpError
from api_clients.leetcode import LeetCodeAPI
from tools.models import RichToolDescription
from mcp_instance import mcp

# --- TOOL: Get LeetCode Daily Problem ---
LeetCodeDailyDesc = RichToolDescription(
    description="Retrieves today's official LeetCode Daily Coding Challenge including problem title, difficulty level, complete problem description, and direct link to solve. Automatically formats the problem description from HTML to readable text with proper formatting for code examples and constraints. Perfect for daily practice routine.",
    use_when="User wants today's practice problem, daily coding challenge, or uses phrases like 'daily problem', 'LeetCode daily', 'today's LeetCode', 'daily challenge', 'what's the problem today', 'daily coding problem', or 'LeetCode POTD (Problem of the Day)'.",
    side_effects="Makes a network request to the LeetCode GraphQL API to fetch current daily challenge. Response time typically 1-3 seconds. Converts HTML content to readable format."
)

@mcp.tool(description=LeetCodeDailyDesc.model_dump_json())
async def get_leetcode_daily_problem() -> str:
    try:
        result = await LeetCodeAPI.get_daily_problem()
        question_data = result.get("activeDailyCodingChallengeQuestion", {})
        if not question_data:
            return "😕 Could not fetch the LeetCode daily problem."

        question = question_data['question']
        title = question['title']
        difficulty = question['difficulty']
        url = f"https://leetcode.com{question_data['link']}"
        # Get raw HTML content from LeetCode API
        raw_content = question['content']
        # Format for WhatsApp after receiving from API
        content = format_for_whatsapp(raw_content)

        response = f"*Today's LeetCode Daily Problem*\n\n"
        response += f"*{title}* ({difficulty})\n"
        response += f"Solve it here: {url}\n\n"
        response += f"Problem Description:\n{content}"

        return response
    except Exception as e:
        raise McpError(ErrorData(code=500, message=f"❌ Error fetching LeetCode daily problem: {str(e)}"))