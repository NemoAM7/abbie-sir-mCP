from fastmcp import mcp_tool
from textwrap import dedent

@mcp_tool
async def about() -> dict[str, str]:
    """
    Provides comprehensive information about the Competitive Programming Assistant,
    its capabilities, supported platforms, and how to get started. Essential reference
    for new users to understand all available features and commands.
    
    Use when: User asks 'what can you do', 'help', 'about', 'features', 'commands',
    'how to use', 'what platforms', or needs an overview of capabilities.
    """
    server_name = "Competitive Programming Assistant"
    server_description = dedent("""
    Competitive Programming Assistant gives you contest problems, user stats, and contest info from Codeforces, LeetCode, CodeChef, AtCoder, TopCoder, and CodingNinjas.

    Main features:
    - Get user stats
    - Track ratings
    - Recommend problems
    - Find contests

    Example: "Show my Codeforces stats", "Recommend problems", "Upcoming contests"
    """)
    return {
        "name": server_name,
        "description": server_description
    }