# File: gemini_tool_definitions.py
#
# This file contains the corrected tool definitions for the Gemini model.
# All `type` values have been converted to UPPERCASE to match the
# google-generativeai library's required format.

mcp_tool_definitions = [
    # --- Validation Tool ---
    {
        "name": "validate",
        "description": "A simple tool to validate the server is responsive and authenticated.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        }
    },

    # --- LeetCode Tools ---
    {
        "name": "get_leetcode_daily_problem",
        "description": "Fetches today's LeetCode Daily Coding Challenge problem. Use when user asks for 'leetcode daily', 'today's problem', 'daily challenge', or similar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        }
    },

    # --- Contest Tools ---
    {
        "name": "get_upcoming_contests",
        "description": "Fetches upcoming programming contests from various platforms. Use when user asks about 'contests', 'upcoming contests', 'when is next contest', or mentions specific platforms like codeforces, leetcode, atcoder, etc.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "platforms": {
                    "type": "ARRAY",
                    "description": "List of contest platforms to check. Default: ['codeforces', 'leetcode', 'codechef']",
                    "items": {"type": "STRING"}
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Maximum number of contests to return. Default: 10"
                }
            }
        }
    },
    {
        "name": "generate_contest_calendar",
        "description": "Generates a downloadable iCalendar (.ics) file for upcoming contests from specified platforms.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "platforms": {
                    "type": "ARRAY",
                    "description": "A list of platforms to include in the calendar file.",
                    "items": {"type": "STRING"}
                }
            }
        }
    },

    # --- Codeforces Text-Based Tools ---
    {
        "name": "get_codeforces_user_stats",
        "description": "Fetches detailed Codeforces stats, rating, rank, and profile information for one or more users. Use this when user asks about someone's rating, rank, stats, profile, or mentions a Codeforces handle/username. Examples: 'tourist rating', 'benq stats', 'my codeforces profile', 'compare tourist and benq'.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handles": {
                    "type": "ARRAY",
                    "description": "A list of Codeforces user handles/usernames to get stats for.",
                    "items": {"type": "STRING"}
                }
            }
        }
    },
    {
        "name": "recommend_problems",
        "description": "Recommends unsolved Codeforces problems based on a user's rating or a specified difficulty.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handle": {
                    "type": "STRING",
                    "description": "The Codeforces handle to find unsolved problems for. Defaults to the configured handle."
                },
                "min_rating": {
                    "type": "INTEGER",
                    "description": "The minimum rating for recommended problems. Defaults to the user's current rating."
                },
                "max_rating": {
                    "type": "INTEGER",
                    "description": "The maximum rating for recommended problems. Defaults to the user's current rating + 199."
                },
                "count": {
                    "type": "INTEGER",
                    "description": "Number of problems to recommend. Defaults to 5."
                }
            }
        }
    },
    {
        "name": "get_solved_problems",
        "description": "Shows a list of the most recently solved problems for a given Codeforces handle.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handle": {
                    "type": "STRING",
                    "description": "The user's Codeforces handle. Defaults to the configured handle."
                },
                "count": {
                    "type": "INTEGER",
                    "description": "Number of problems to show. Defaults to 10."
                }
            }
        }
    },
    {
        "name": "get_rating_changes",
        "description": "Shows the rating changes for a user from their most recent rated contests.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handle": {
                    "type": "STRING",
                    "description": "The user's Codeforces handle. Defaults to the configured handle."
                },
                "count": {
                    "type": "INTEGER",
                    "description": "Number of recent contests to show changes for. Defaults to 5."
                }
            }
        }
    },
    {
        "name": "get_solved_rating_histogram",
        "description": "Displays a text-based histogram of solved problem ratings, showing a user's strengths and weaknesses.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handle": {
                    "type": "STRING",
                    "description": "The user's Codeforces handle. Defaults to the configured handle."
                },
                "bin_size": {
                    "type": "INTEGER",
                    "description": "The size of each rating bin (e.g., 100 or 200). Defaults to 100."
                }
            }
        }
    },
    {
        "name": "get_upsolve_targets",
        "description": "Finds contests where the user has few unsolved problems, making them good targets for upsolving.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handle": {
                    "type": "STRING",
                    "description": "The user's Codeforces handle. Defaults to the configured handle."
                },
                "count": {
                    "type": "INTEGER",
                    "description": "Number of contest targets to show. Defaults to 5."
                }
            }
        }
    },

    # --- Codeforces Graphing/Image Tools ---
    {
        "name": "plot_rating_graph",
        "description": "Generates and displays a plot of rating history for one or more Codeforces users.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handles": {
                    "type": "ARRAY",
                    "description": "A list of Codeforces user handles to plot on the graph.",
                    "items": {"type": "STRING"}
                }
            }
        }
    },
    {
        "name": "plot_solved_rating_distribution",
        "description": "Displays a graphical histogram (a bar chart) of solved problem ratings for a user.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handle": {
                    "type": "STRING",
                    "description": "The user's Codeforces handle. Defaults to the configured handle."
                }
            }
        }
    },
    {
        "name": "plot_verdict_distribution",
        "description": "Generates a pie chart of a user's submission verdicts (e.g., OK, WRONG_ANSWER).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handle": {
                    "type": "STRING",
                    "description": "The user's Codeforces handle. Defaults to the configured handle."
                }
            }
        }
    },
    {
        "name": "plot_tag_distribution",
        "description": "Generates a bar chart of a user's most solved problem tags (e.g., dp, graphs, math).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handle": {
                    "type": "STRING",
                    "description": "The user's Codeforces handle. Defaults to the configured handle."
                },
                "count": {
                    "type": "INTEGER",
                    "description": "Number of top tags to show in the chart. Defaults to 15."
                }
            }
        }
    },
    {
        "name": "plot_language_distribution",
        "description": "Generates a pie chart of the programming languages a user submits with (e.g., C++, Python).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "handle": {
                    "type": "STRING",
                    "description": "The user's Codeforces handle. Defaults to the configured handle."
                }
            }
        }
    }
]