from fastmcp import mcp_tool
from textwrap import dedent

@mcp_tool
async def about() -> dict[str, str]:
    server_name = "Competitive Programming Assistant"
    server_description = dedent("""
    Welcome to your Competitive Programming Assistant!

    This bot is designed to help you at every step of your competitive programming journey. Here’s what it can do for you:
    - Find and explain problems from popular sites like Codeforces and LeetCode.
    - Show you today's LeetCode Daily Challenge.
    - Track upcoming contests and help you prepare with a contest calendar.
    - Give you stats, ratings, and progress for Codeforces users.
    - Recommend new problems to solve based on your level.
    - Show which problems youve solved and where you can improve.
    - Visualize your progress with graphs and charts (like rating history, solved problems, and more).
    - Help you upsolve contests and find good practice targets.
    - Review your code and suggest improvements.
    - Answer your questions about programming, contests, and strategies.

    Just ask for help with a problem, contest, or your progress, and this assistant will guide you step by step!
    Start by asking something like "I am @username and I need help with a problem or give my codeforces stats"
    """)
    return {
        "name": server_name,
        "description": server_description
    }