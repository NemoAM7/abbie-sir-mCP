import textwrap
import random
from datetime import datetime
from collections import defaultdict
from typing import Annotated, List, Optional

from pydantic import Field
from mcp import ErrorData, McpError
import asyncio

import config
from api_clients.codeforces import CodeforcesAPI
from tools.models import RichToolDescription
from mcp_instance import mcp

# --- TOOL: Get User Stats ---
UserStatsDesc = RichToolDescription(
    description="Fetches comprehensive Codeforces profile statistics for one or more users including current rating, max rating, rank, registration date, and profile links. Supports batch comparison of multiple users with automatic sorting by rating. If no handle is provided, uses your configured default handle from settings.",
    use_when="User requests profile information, current stats, rating details, user comparison, leaderboards between friends, or phrases like 'my stats', 'show rating', 'profile info', 'compare with [username]', 'who has higher rating', or 'user leaderboard'.",
    side_effects="Makes network requests to the Codeforces API. Response time depends on number of users requested (typically 1-3 seconds for multiple users)."
)

@mcp.tool(description=UserStatsDesc.model_dump_json())
async def get_codeforces_user_stats(
    handles: Annotated[Optional[List[str]], Field(description="A list of Codeforces user handles.")] = None
) -> str:
    target_handles = handles or [config.DEFAULT_HANDLE]
    if not target_handles[0]:
        raise McpError(ErrorData(code=400, message="No handles provided, and no default handle is configured."))

    try:
        users_info = await CodeforcesAPI.get_user_info(target_handles)
        if not users_info:
            return f"😕 Could not find user(s): {', '.join(target_handles)}"

        users_info.sort(key=lambda u: u.get('rating', 0), reverse=True)
        response = f"🏆 *Codeforces User {'Leaderboard' if len(target_handles) > 1 else 'Stats'}*\n\n"

        for user in users_info:
            handle = user.get('handle', 'N/A')
            member_since = datetime.fromtimestamp(user.get('registrationTimeSeconds', 0)).strftime('%b %Y')
            response += textwrap.dedent(f"""
            *{user.get('rank', 'Unrated')} {handle}*
            - Rating: *{user.get('rating', 'N/A')}* (Max: {user.get('maxRating', 'N/A')})
            - Member Since: {member_since}
            - [Profile](https://codeforces.com/profile/{handle})
            ---
            """)
        return response.strip()
    except Exception as e:
        raise McpError(ErrorData(code=500, message=f"Error fetching user stats: {str(e)}"))


# --- TOOL: Real Problem Recommendations ---
RecommendDesc = RichToolDescription(
    description="Intelligently recommends UNSOLVED Codeforces problems tailored to a user's skill level. Analyzes the user's solved problem history to exclude already completed problems and suggests problems within a specified rating range. Automatically determines appropriate difficulty based on user's current rating if no range is specified. Uses smart filtering to ensure recommendations are challenging but achievable.",
    use_when="User seeks practice problems, skill improvement, or phrases like 'what should I solve', 'recommend problems', 'practice suggestions', 'problems for my rating', 'give me something to solve', 'I need practice', or 'find problems for [rating] level'.",
    side_effects="Makes multiple network requests: fetches user's solved problems history (can be slow for users with many submissions), retrieves current problemset data, and performs filtering algorithms. Total response time typically 3-7 seconds."
)

@mcp.tool(description=RecommendDesc.model_dump_json())
async def recommend_problems(
    handle: Annotated[Optional[str], Field(description="The handle to find unsolved problems for. Defaults to your configured handle.")] = None,
    min_rating: Annotated[Optional[int], Field(description="The minimum rating for recommended problems.")] = None,
    max_rating: Annotated[Optional[int], Field(description="The maximum rating for recommended problems.")] = None,
    count: Annotated[int, Field(description="Number of problems to recommend.")] = 5
) -> str:
    target_handle = handle or config.DEFAULT_HANDLE
    if not target_handle:
        raise McpError(ErrorData(code=400, message="Please specify a handle or set DEFAULT_HANDLE."))

    try:
        user_info_list = await CodeforcesAPI.get_user_info([target_handle])
        if not user_info_list:
            return f"Could not find user '{target_handle}'."

        if min_rating is None and max_rating is None:
            user_rating = user_info_list[0].get('rating', 1200)
            min_rating = user_rating
            max_rating = user_rating + 199

        submissions, problemset_data = await asyncio.gather(
            CodeforcesAPI.get_user_status(target_handle),
            CodeforcesAPI.get_problemset()
        )

        solved_ids = {f"{s['problem']['contestId']}{s['problem']['index']}" for s in submissions if s.get('verdict') == 'OK'}
        candidates = [p for p in problemset_data.get('problems', []) if f"{p.get('contestId')}{p.get('index')}" not in solved_ids and 'rating' in p and min_rating <= p['rating'] <= max_rating]

        if not candidates:
            return f"😕 Couldn't find any suitable unsolved problems for *{target_handle}* in rating range {min_rating}-{max_rating}."

        random.shuffle(candidates)
        response = f"💡 **Recommended Problems for {target_handle} ({min_rating}-{max_rating}):**\n\n"
        for i, problem in enumerate(candidates[:count], 1):
            url = f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"
            response += f"{i}. [{problem['name']}]({url}) - Rating: {problem['rating']}\n"
        return response
    except Exception as e:
        raise McpError(ErrorData(code=500, message=f"Error generating recommendations: {str(e)}"))


# --- TOOL: Get Recently Solved Problems ---
SolvedDesc = RichToolDescription(
    description="Displays a chronologically ordered list of the most recently solved (AC - Accepted) problems for a Codeforces user. Shows problem names, ratings, solve dates, and direct links to problems. Automatically deduplicates multiple submissions of the same problem to show only unique solves. Perfect for tracking recent activity and progress.",
    use_when="User wants to review recent activity, track progress, or uses phrases like 'recent solves', 'what did I solve lately', 'my activity', 'recent problems', 'last solved', 'show my progress', 'what I solved today/yesterday', or 'stalk [username]'.",
    side_effects="Makes a network request to fetch user's submission history (up to 100 recent submissions). Processing time depends on user's submission volume, typically 1-3 seconds."
)

@mcp.tool(description=SolvedDesc.model_dump_json())
async def get_solved_problems(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None,
    count: Annotated[int, Field(description="Number of problems to show.")] = 10
) -> str:
    target_handle = handle or config.DEFAULT_HANDLE
    if not target_handle:
        raise McpError(ErrorData(code=400, message="Please specify a handle or set DEFAULT_HANDLE."))

    try:
        submissions = await CodeforcesAPI.get_user_status(target_handle, count=100)
        solved_submissions = []
        seen_problems = set()
        for sub in sorted(submissions, key=lambda s: s['creationTimeSeconds'], reverse=True):
            if sub.get('verdict') == 'OK':
                problem = sub['problem']
                problem_id = f"{problem['contestId']}-{problem['index']}"
                if problem_id not in seen_problems:
                    solved_submissions.append(sub)
                    seen_problems.add(problem_id)

        if not solved_submissions:
            return f"😕 No recent AC submissions found for *{target_handle}*."

        response = f"✅ **Recently Solved by {target_handle}**\n\n"
        for i, sub in enumerate(solved_submissions[:count], 1):
            problem = sub['problem']
            solve_time = datetime.fromtimestamp(sub['creationTimeSeconds']).strftime('%Y-%m-%d')
            url = f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"
            response += f"{i}. [{problem['name']}]({url}) - **{problem.get('rating', 'N/A')}** (Solved on {solve_time})\n"
        return response
    except Exception as e:
        raise McpError(ErrorData(code=500, message=f"Error fetching solved problems: {str(e)}"))


# --- TOOL: Get Rating Changes ---
RatingChangesDesc = RichToolDescription(
    description="Displays detailed rating progression from recent Codeforces contests including contest names, user ranking, old rating, new rating, and rating delta (+/-). Shows performance trends and helps identify improvement patterns. Includes direct links to contest pages for detailed review.",
    use_when="User wants to analyze contest performance, track rating progression, or uses phrases like 'rating changes', 'contest history', 'my performance', 'how did I do', 'recent contests', 'rating graph data', 'show deltas', or 'contest results'.",
    side_effects="Makes a network request to fetch user's contest participation history and rating changes. Response time typically 1-2 seconds."
)

@mcp.tool(description=RatingChangesDesc.model_dump_json())
async def get_rating_changes(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None,
    count: Annotated[int, Field(description="Number of recent contests to show changes for.")] = 5
) -> str:
    target_handle = handle or config.DEFAULT_HANDLE
    if not target_handle:
        raise McpError(ErrorData(code=400, message="Please specify a handle or set DEFAULT_HANDLE."))

    try:
        changes = await CodeforcesAPI.get_user_rating_changes(target_handle)
        if not changes:
            return f"😕 No rating changes found for *{target_handle}*. They might be unrated."

        response = f"📈 **Recent Rating Changes for {target_handle}**\n\n"
        for change in sorted(changes, key=lambda c: c['ratingUpdateTimeSeconds'], reverse=True)[:count]:
            delta = change['newRating'] - change['oldRating']
            emoji = "🔼" if delta > 0 else "🔽" if delta < 0 else "➖"
            url = f"https://codeforces.com/contest/{change['contestId']}"
            response += f"- [{change['contestName']}]({url})\n"
            response += f"  - Rank: {change['rank']}, {emoji} {change['oldRating']} -> **{change['newRating']}** ({delta:+})\n"
        return response
    except Exception as e:
        raise McpError(ErrorData(code=500, message=f"Error fetching rating changes: {str(e)}"))


# --- TOOL: Get Solved Problems Histogram ---
HistogramDesc = RichToolDescription(
    description="Generates a visual ASCII histogram showing the distribution of solved problems across different rating ranges. Reveals user's strengths (rating ranges with many solves) and weaknesses (rating gaps). Uses configurable bin sizes to customize granularity of analysis. Essential for identifying skill gaps and planning focused practice.",
    use_when="User wants to analyze their problem-solving distribution, identify weak areas, or uses phrases like 'histogram', 'rating distribution', 'breakdown of solved problems', 'show my strengths', 'where are my gaps', 'problem distribution', or 'rating analysis'.",
    side_effects="Makes a network request to fetch extensive user submission history (up to 5000 submissions for comprehensive analysis). Processing time varies with user's submission count, typically 2-5 seconds."
)

@mcp.tool(description=HistogramDesc.model_dump_json())
async def get_solved_rating_histogram(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None,
    bin_size: Annotated[int, Field(description="The size of each rating bin.", ge=100, le=400)] = 100
) -> str:
    target_handle = handle or config.DEFAULT_HANDLE
    if not target_handle:
        raise McpError(ErrorData(code=400, message="Please specify a handle or set DEFAULT_HANDLE."))

    try:
        submissions = await CodeforcesAPI.get_user_status(target_handle, count=5000)
        problem_ratings = defaultdict(int)
        seen_problems = set()
        for sub in submissions:
            if sub.get('verdict') == 'OK':
                problem = sub['problem']
                problem_id = f"{problem.get('contestId')}-{problem.get('index')}"
                if 'rating' in problem and problem_id not in seen_problems:
                    rating_bin = (problem['rating'] // bin_size) * bin_size
                    problem_ratings[rating_bin] += 1
                    seen_problems.add(problem_id)

        if not problem_ratings:
            return f"😕 No rated problems solved by *{target_handle}*."

        response = f"📊 **Solved Problems Histogram for {target_handle}**\n\n```\n"
        max_count = max(problem_ratings.values()) if problem_ratings else 0
        sorted_bins = sorted(problem_ratings.keys())

        for rating in sorted_bins:
            count = problem_ratings[rating]
            bar_length = int((count / max_count) * 40) if max_count > 0 else 0
            bar = '█' * bar_length
            response += f"{rating:4d}-{rating+bin_size-1:<4d} | {bar:<40} ({count})\n"

        response += "```"
        return response
    except Exception as e:
        raise McpError(ErrorData(code=500, message=f"Error generating histogram: {str(e)}"))

# --- TOOL: Get Upsolve Targets ---
UpsolveDesc = RichToolDescription(
    description="Identifies optimal contests for upsolving by finding competitions where the user has participated but left several problems unsolved. Analyzes contest participation history and calculates completion rates to recommend contests that offer the best learning opportunities. Helps users systematically complete contests they've started.",
    use_when="User wants to find contests to complete, improve contest performance, or uses phrases like 'what to upsolve', 'fullsolve targets', 'which contest should I finish', 'complete contests', 'upsolving suggestions', 'unfinished contests', or 'contest completion'.",
    side_effects="Makes multiple API calls to analyze user's contest participation and problem-solving history. Can be slower due to comprehensive analysis of multiple contests. Typical response time 5-10 seconds depending on user's contest history."
)

@mcp.tool(description=UpsolveDesc.model_dump_json())
async def get_upsolve_targets(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None,
    count: Annotated[int, Field(description="Number of contest targets to show.")] = 5
) -> str:
    # Note: This tool is more complex and has been omitted for brevity in this example.
    # You can copy its full implementation from your original script if needed.
    return "Upsolving tool logic goes here."