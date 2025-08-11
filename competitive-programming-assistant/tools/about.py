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
    🏆 *Welcome to your Competitive Programming Assistant!*

    Your AI companion for competitive programming success! Here's what I can do:

    📊 *Profile & Stats*
    • Get Codeforces user stats & ratings
    • Compare multiple users side-by-side  
    • Track rating changes & contest performance
    • Monitor recent solved problems

    🎯 *Smart Recommendations*
    • Get unsolved problems for your level
    • Auto-adjust difficulty based on your rating
    • Find practice problems to improve skills
    • Identify weak areas in your solving

    📈 *Visual Analysis*
    • Rating graphs over time
    • Problem difficulty distribution charts
    • Tag/topic strength analysis
    • Submission accuracy pie charts
    • Programming language usage stats

    🏁 *Contest Info*
    • Upcoming contests from all major platforms
    • Codeforces, LeetCode, CodeChef, AtCoder, TopCoder
    • Contest start times & registration links
    • Find contests to upsolve & complete

    🧠 *Daily Practice*
    • Today's LeetCode Daily Challenge
    • Problem discovery across platforms
    • Skill assessment & improvement tracking

    🚀 *Quick Start Commands:*

    _For Stats:_
    "Show my Codeforces stats"
    "I am [username], show my profile"

    _For Practice:_
    "Recommend problems for my level"
    "What's today's LeetCode daily?"
    "What should I practice?"

    _For Contests:_
    "What contests are upcoming?"
    "When is the next contest?"

    _For Analysis:_
    "Plot my rating graph"
    "Show my tag distribution"
    "I am [username], compare me with [username]"

    🔧 *Supported Platforms:*
    Codeforces, LeetCode, CodeChef, AtCoder, TopCoder, CodingNinjas

    💡 *Pro Tip:* Set your default handle for easier access!

    *Ready to boost your CP journey? Just ask me anything!* 🚀
    """)
    return {
        "name": server_name,
        "description": server_description
    }