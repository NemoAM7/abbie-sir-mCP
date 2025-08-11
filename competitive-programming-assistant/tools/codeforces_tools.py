import asyncio
import base64
import io
import textwrap
import random
from collections import defaultdict
from datetime import datetime
from typing import Annotated, List, Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydantic import Field
from mcp import ErrorData, McpError
from mcp.types import TextContent, ImageContent

import config
from api_clients.codeforces import CodeforcesAPI
from tools.models import RichToolDescription
from mcp_instance import mcp

# --- Helper Functions ---

def _get_rank_color(rank: str) -> tuple:
    """Returns RGB color tuple based on Codeforces rank."""
    rank_colors = {
        'newbie': (128, 128, 128),           # Gray
        'pupil': (0, 128, 0),                # Green
        'specialist': (3, 168, 158),         # Cyan
        'expert': (0, 0, 255),               # Blue
        'candidate master': (170, 0, 170),   # Violet
        'master': (255, 140, 0),             # Orange
        'international master': (255, 140, 0), # Orange
        'grandmaster': (255, 0, 0),          # Red
        'international grandmaster': (255, 0, 0), # Red
        'legendary grandmaster': (255, 0, 0)  # Red
    }
    return rank_colors.get(rank.lower(), (128, 128, 128))

def _create_gradient_background(width: int, height: int, color1: tuple, color2: tuple) -> Image.Image:
    """Creates a gradient background image."""
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def _get_default_font(size: int) -> ImageFont.FreeTypeFont:
    """Gets default font, falls back to PIL default if system fonts unavailable."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        try:
            return ImageFont.truetype("/System/Library/Fonts/Arial.ttf", size)
        except:
            return ImageFont.load_default()

def _draw_progress_bar(draw: ImageDraw.Draw, x: int, y: int, width: int, height: int, 
                      progress: float, bg_color: tuple, fill_color: tuple):
    """Draws a progress bar."""
    # Background
    draw.rectangle([x, y, x + width, y + height], fill=bg_color, outline=(200, 200, 200))
    # Progress fill
    fill_width = int(width * min(progress, 1.0))
    if fill_width > 0:
        draw.rectangle([x, y, x + fill_width, y + height], fill=fill_color)

def _image_to_base64(image: Image.Image) -> str:
    """Converts PIL Image to base64 string."""
    buf = io.BytesIO()
    image.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def _create_image_response(text: str, image_base64: str) -> List[TextContent | ImageContent]:
    """Creates the standard MCP response format for an image using proper MCP types."""
    return [
        TextContent(type="text", text=text), 
        ImageContent(type="image", mimeType="image/png", data=image_base64)
    ]

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



# --- TOOL: Compare Users ---
ComparisonDesc = RichToolDescription(
    description="Performs comprehensive comparison between multiple Codeforces users with detailed metrics including ratings, contest performance, activity levels, and improvement trends. Handles edge cases like invalid handles, inactive users, or API failures gracefully with clear error messages.",
    use_when="User wants to compare multiple competitive programmers, create leaderboards, analyze relative performance, or uses phrases like 'compare us', 'compare me with [name]', 'who is better', 'leaderboard between friends', 'rank us', 'performance comparison', 'who has better stats', 'how do I stack up', 'compare handles', 'user vs user', 'show comparison', 'analyze together', 'who's winning', 'rate comparison', 'contest comparison', 'skill comparison', 'check standings', 'measure against', 'benchmark users', 'head to head', 'versus analysis', or any request involving multiple usernames/handles for comparison purposes.",
    side_effects="Makes multiple API calls to gather comprehensive data for all users. Response time scales with number of users (3-8 seconds for 3 users). Handles API failures and missing data gracefully."
)

@mcp.tool(description=ComparisonDesc.model_dump_json())
async def compare_codeforces_users(
    handles: Annotated[List[str], Field(description="List of Codeforces handles to compare")]
) -> str:
    if not handles or len(handles) < 2:
        return "❌ Please provide at least 2 handles to compare."
    
    try:
        # Get basic user info
        users_info = await CodeforcesAPI.get_user_info(handles)
        
        # Handle missing users gracefully
        found_handles = {user['handle'].lower() for user in users_info} if users_info else set()
        missing_handles = [h for h in handles if h.lower() not in found_handles]
        
        if missing_handles:
            return f"❌ Could not find the following users: {', '.join(missing_handles)}\n\nPlease check if these handles exist on Codeforces."
        
        if not users_info:
            return "❌ No valid users found. Please check the handles and try again."
        
        # Detailed comparison analysis
        comparison_data = []
        for user in users_info:
            handle = user['handle']
            try:
                # Get additional data for each user
                rating_changes = await CodeforcesAPI.get_user_rating_changes(handle)
                recent_submissions = await CodeforcesAPI.get_user_status(handle, count=50)
                
                # Calculate metrics
                metrics = {
                    'handle': handle,
                    'current_rating': user.get('rating', 0),
                    'max_rating': user.get('maxRating', 0),
                    'rank': user.get('rank', 'Unrated'),
                    'contests_count': len(rating_changes) if rating_changes else 0,
                    'recent_activity': len([s for s in recent_submissions if s.get('verdict') == 'OK']) if recent_submissions else 0,
                    'registration_date': datetime.fromtimestamp(user.get('registrationTimeSeconds', 0)),
                    'last_rating_change': rating_changes[-1] if rating_changes else None
                }
                comparison_data.append(metrics)
                
            except Exception as e:
                # Handle individual user API failures
                metrics = {
                    'handle': handle,
                    'current_rating': user.get('rating', 0),
                    'max_rating': user.get('maxRating', 0),
                    'rank': user.get('rank', 'Unrated'),
                    'contests_count': 'N/A',
                    'recent_activity': 'N/A',
                    'registration_date': datetime.fromtimestamp(user.get('registrationTimeSeconds', 0)),
                    'error': f"Limited data due to API issues"
                }
                comparison_data.append(metrics)
        
        # Sort by current rating
        comparison_data.sort(key=lambda x: x['current_rating'], reverse=True)
        
        # Generate comparison report (WhatsApp formatted)
        response = "🏆 *Competitive Programming Comparison*\n\n"
        
        for i, user in enumerate(comparison_data, 1):
            position_emoji = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            
            response += f"{position_emoji} *{user['rank']} {user['handle']}*\n"
            response += f"   • Current Rating: *{user['current_rating']}*\n"
            response += f"   • Peak Rating: *{user['max_rating']}*\n"
            response += f"   • Contests Participated: {user['contests_count']}\n"
            response += f"   • Recent AC Problems: {user['recent_activity']}\n"
            response += f"   • Member Since: {user['registration_date'].strftime('%b %Y')}\n"
            
            if 'error' in user:
                response += f"   • ⚠️ {user['error']}\n"
            
            response += "\n"
        
        # Add final verdict
        winner = comparison_data[0]
        response += f"🎯 *Final Verdict*: _{winner['handle']}_ leads with {winner['current_rating']} rating!\n\n"
        
        # Add insights
        response += "📊 *Key Insights*:\n"
        rating_gap = comparison_data[0]['current_rating'] - comparison_data[-1]['current_rating']
        response += f"• Rating spread: {rating_gap} points\n"
        
        most_active = max(comparison_data, key=lambda x: x['recent_activity'] if isinstance(x['recent_activity'], int) else 0)
        if isinstance(most_active['recent_activity'], int):
            response += f"• Most active solver: _{most_active['handle']}_ ({most_active['recent_activity']} recent ACs)\n"
        
        return response
        
    except Exception as e:
        return f"❌ *Comparison failed*: {str(e)}\n\nThis might be due to:\n• Network connectivity issues\n• Codeforces API being temporarily unavailable\n• Invalid handle formats\n\nPlease try again in a few moments."

# --- TOOL: Show Bot Capabilities ---
CapabilitiesDesc = RichToolDescription(
    description="Displays a comprehensive overview of the competitive programming assistant's capabilities, available commands, and example usage patterns. Perfect for new users or when someone needs a refresher on what the bot can do.",
    use_when="User sends basic greetings or requests help, such as 'hi', 'hello', 'help', 'what can you do', 'commands', 'features', 'capabilities', 'how to use', or any general inquiry about bot functionality.",
    side_effects="No API calls - displays static information about available features and tools."
)

@mcp.tool(description=CapabilitiesDesc.model_dump_json())
async def show_bot_capabilities() -> str:
    return """👋 *Welcome to your Competitive Programming Assistant!*

I'm here to help you with Codeforces analysis and improvement. Here's what I can do:

🏆 *Profile & Stats*
• my stats - View your current rating, rank, and profile info
• compare me with [username] - Head-to-head comparison with other users
• leaderboard [user1] [user2] [user3] - Create rankings between friends

📊 *Performance Analysis*
• rating changes - See your recent contest performance and rating deltas
• histogram - Visual breakdown of solved problems by rating range
• recent solves - Track your latest accepted solutions

💡 *Practice & Improvement*
• recommend problems - Get personalized problem suggestions for your level
• problems for [rating] - Find practice problems in specific rating ranges
• what to upsolve - Discover contests worth completing

🎯 *Activity Tracking*
• recent activity - Monitor your solving patterns
• stalk [username] - Check what others have been solving lately

*💬 Quick Examples:*
• "Show my Codeforces stats"
• "Recommend 5 problems around 1400 rating"
• "Compare me with tourist and Errichto"
• "What did I solve this week?"
• "Show rating histogram with 200-point bins"

*🚀 Pro Tips:*
• Set your default handle in config to avoid typing it repeatedly
• Use specific rating ranges for targeted practice
• Check histograms to identify skill gaps
• Compare with friends to stay motivated!

Just ask me anything about Codeforces analysis - I'm here to help you improve! 🚀"""

# --- TOOL: Generate Profile Card ---

ProfileCardDesc = RichToolDescription(
    description="Generates a visually appealing Codeforces profile card showing key stats, rating, and achievements.",
    use_when="User asks to 'generate profile card', 'make profile image', 'create profile snippet', or 'share my profile'.",
    side_effects="Makes network requests to Codeforces API and generates a profile card image."
)

@mcp.tool(description=ProfileCardDesc.model_dump_json())
async def generate_profile_card(
    handle: Annotated[Optional[str], Field(description="The Codeforces handle. Defaults to your configured handle.")] = None,
    style: Annotated[str, Field(description="Card style: 'modern', 'minimal', 'dark', or 'achievement'.")] = "modern",
    include_graph: Annotated[bool, Field(description="Whether to include a mini rating graph.")] = True
) -> List[TextContent | ImageContent]:
    
    target_handle = handle or config.DEFAULT_HANDLE
    if not target_handle:
        raise McpError(ErrorData(code=400, message="Please specify a handle or set DEFAULT_HANDLE."))
    
    try:
        # Fetch user data
        user_info_list, rating_changes, submissions = await asyncio.gather(
            CodeforcesAPI.get_user_info([target_handle]),
            CodeforcesAPI.get_user_rating_changes(target_handle),
            CodeforcesAPI.get_user_status(target_handle, count=1000)
        )
        
        if not user_info_list:
            raise McpError(ErrorData(code=404, message=f"User '{target_handle}' not found."))
        
        user_info = user_info_list[0]
        
        # Calculate stats
        solved_problems = set()
        for sub in submissions:
            if sub.get('verdict') == 'OK':
                problem = sub['problem']
                solved_problems.add(f"{problem.get('contestId')}-{problem.get('index')}")
        
        total_solved = len(solved_problems)
        current_rating = user_info.get('rating', 0)
        max_rating = user_info.get('maxRating', current_rating)
        rank = user_info.get('rank', 'Unrated')
        member_since = datetime.fromtimestamp(user_info.get('registrationTimeSeconds', 0))
        
        # Create card based on style
        if style == "dark":
            width, height = 800, 500
            bg_color1 = (30, 30, 40)
            bg_color2 = (50, 50, 60)
            text_color = (255, 255, 255)
            accent_color = _get_rank_color(rank)
        elif style == "minimal":
            width, height = 700, 400
            bg_color1 = (250, 250, 250)
            bg_color2 = (240, 240, 240)
            text_color = (50, 50, 50)
            accent_color = _get_rank_color(rank)
        else:  # modern or achievement
            width, height = 850, 550
            bg_color1 = (245, 245, 250)
            bg_color2 = (235, 235, 245)
            text_color = (40, 40, 40)
            accent_color = _get_rank_color(rank)
        
        # Create base image
        image = _create_gradient_background(width, height, bg_color1, bg_color2)
        draw = ImageDraw.Draw(image)
        
        # Fonts
        title_font = _get_default_font(36)
        header_font = _get_default_font(24)
        text_font = _get_default_font(18)
        small_font = _get_default_font(14)
        
        # Draw main content
        y_offset = 40
        
        # Header with handle and rank
        draw.text((40, y_offset), target_handle, font=title_font, fill=accent_color)
        rank_text = f"{rank.title()}"
        draw.text((40, y_offset + 50), rank_text, font=header_font, fill=text_color)
        
        # Rating section
        y_offset += 120
        draw.text((40, y_offset), "Rating", font=header_font, fill=text_color)
        
        rating_text = f"Current: {current_rating}"
        if max_rating != current_rating:
            rating_text += f" (Max: {max_rating})"
        draw.text((40, y_offset + 35), rating_text, font=text_font, fill=accent_color)
        
        # Progress bar for rating (assuming 3000 as max for visualization)
        _draw_progress_bar(draw, 40, y_offset + 70, 300, 15, current_rating/3000, 
                          (200, 200, 200), accent_color)
        
        # Stats section
        y_offset += 120
        draw.text((40, y_offset), "Statistics", font=header_font, fill=text_color)
        
        stats_text = f"Problems Solved: {total_solved}"
        draw.text((40, y_offset + 35), stats_text, font=text_font, fill=text_color)
        
        member_text = f"Member Since: {member_since.strftime('%B %Y')}"
        draw.text((40, y_offset + 65), member_text, font=text_font, fill=text_color)
        
        if rating_changes:
            contests_count = len(rating_changes)
            draw.text((40, y_offset + 95), f"Contests: {contests_count}", font=text_font, fill=text_color)
        
        # Mini rating graph if requested and data available
        if include_graph and rating_changes and len(rating_changes) > 1:
            graph_x, graph_y = width - 320, 50
            graph_width, graph_height = 280, 150
            
            # Draw graph background
            draw.rectangle([graph_x, graph_y, graph_x + graph_width, graph_y + graph_height], 
                          fill=(255, 255, 255, 128), outline=accent_color, width=2)
            
            # Plot rating changes
            sorted_changes = sorted(rating_changes, key=lambda x: x['ratingUpdateTimeSeconds'])
            ratings = [rc['newRating'] for rc in sorted_changes]
            
            if len(ratings) > 1:
                min_rating = min(ratings)
                max_rating_graph = max(ratings)
                rating_range = max_rating_graph - min_rating if max_rating_graph != min_rating else 1
                
                points = []
                for i, rating in enumerate(ratings):
                    x = graph_x + 10 + (i * (graph_width - 20)) // (len(ratings) - 1)
                    y = graph_y + graph_height - 10 - int(((rating - min_rating) / rating_range) * (graph_height - 20))
                    points.append((x, y))
                
                # Draw lines between points
                for i in range(len(points) - 1):
                    draw.line([points[i], points[i + 1]], fill=accent_color, width=2)
                
                # Draw points
                for point in points:
                    draw.ellipse([point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3], fill=accent_color)
        
        # Add decorative elements for achievement style
        if style == "achievement":
            # Add some star decorations
            star_points = [(width - 60, 30), (width - 60, height - 60), (30, height - 60)]
            for x, y in star_points:
                draw.regular_polygon((x, y, 15), 5, fill=accent_color)
        
        # Footer
        footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y')}"
        draw.text((40, height - 40), footer_text, font=small_font, fill=(150, 150, 150))
        
        # Codeforces attribution
        cf_text = "Codeforces Profile"
        draw.text((width - 200, height - 40), cf_text, font=small_font, fill=(150, 150, 150))
        
        # Convert to base64
        image_base64 = _image_to_base64(image)
        
        response_text = f"🎨 **Profile Card Generated for {target_handle}**\n\n"
        response_text += f"📊 **Stats Preview:**\n"
        response_text += f"• Rating: {current_rating} ({rank.title()})\n"
        response_text += f"• Problems Solved: {total_solved}\n"
        response_text += f"• Style: {style.title()}\n\n"
        response_text += "Perfect for sharing on social media! 🚀"
        
        return _create_image_response(response_text, image_base64)
        
    except Exception as e:
        raise McpError(ErrorData(code=500, message=f"❌ Error generating profile card: {str(e)}"))


# --- TOOL: Generate Achievement Card ---

AchievementCardDesc = RichToolDescription(
    description="Creates a special achievement card for milestones like rating increases, problem solving streaks, or rank promotions.",
    use_when="User asks to 'celebrate achievement', 'milestone card', 'rank promotion card', or 'achievement image'.",
    side_effects="Makes network requests to Codeforces API and generates an achievement celebration image."
)

@mcp.tool(description=AchievementCardDesc.model_dump_json())
async def generate_achievement_card(
    handle: Annotated[Optional[str], Field(description="The Codeforces handle. Defaults to your configured handle.")] = None,
    achievement_type: Annotated[str, Field(description="Type of achievement: 'rating_milestone', 'rank_promotion', 'problem_milestone', or 'contest_milestone'.")] = "rating_milestone",
    milestone_value: Annotated[Optional[int], Field(description="The milestone value (e.g., 1500 for rating, 500 for problems).")] = None
) -> List[TextContent | ImageContent]:
    
    target_handle = handle or config.DEFAULT_HANDLE
    if not target_handle:
        raise McpError(ErrorData(code=400, message="Please specify a handle or set DEFAULT_HANDLE."))
    
    try:
        # Fetch user data
        user_info_list, rating_changes, submissions = await asyncio.gather(
            CodeforcesAPI.get_user_info([target_handle]),
            CodeforcesAPI.get_user_rating_changes(target_handle),
            CodeforcesAPI.get_user_status(target_handle, count=2000)
        )
        
        if not user_info_list:
            raise McpError(ErrorData(code=404, message=f"User '{target_handle}' not found."))
        
        user_info = user_info_list[0]
        current_rating = user_info.get('rating', 0)
        rank = user_info.get('rank', 'Unrated')
        
        # Create achievement card (800x600 for celebration)
        width, height = 800, 600
        
        # Golden celebration theme
        bg_color1 = (255, 215, 0, 100)  # Gold
        bg_color2 = (255, 140, 0, 100)  # Dark orange
        
        # Create base with celebration background
        image = Image.new('RGBA', (width, height), (30, 30, 50, 255))
        
        # Add celebration elements
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw celebration rays
        center_x, center_y = width // 2, height // 2
        for i in range(0, 360, 30):
            import math
            x1 = center_x + int(200 * math.cos(math.radians(i)))
            y1 = center_y + int(200 * math.sin(math.radians(i)))
            x2 = center_x + int(300 * math.cos(math.radians(i)))
            y2 = center_y + int(300 * math.sin(math.radians(i)))
            draw.line([(x1, y1), (x2, y2)], fill=(255, 215, 0, 100), width=3)
        
        image = Image.alpha_composite(image, overlay)
        draw = ImageDraw.Draw(image)
        
        # Fonts
        title_font = _get_default_font(48)
        subtitle_font = _get_default_font(28)
        text_font = _get_default_font(20)
        
        # Achievement content based on type
        if achievement_type == "rating_milestone":
            milestone = milestone_value or (current_rating // 100 * 100)
            title = "🎉 MILESTONE ACHIEVED! 🎉"
            subtitle = f"{target_handle} reached {milestone}+ rating!"
            description = f"Current Rating: {current_rating}\nRank: {rank.title()}"
            
        elif achievement_type == "rank_promotion":
            title = "🚀 RANK PROMOTION! 🚀"
            subtitle = f"{target_handle} is now {rank.title()}!"
            description = f"Rating: {current_rating}\nKeep climbing! 📈"
            
        elif achievement_type == "problem_milestone":
            solved_count = len(set(f"{s['problem'].get('contestId')}-{s['problem'].get('index')}" 
                                 for s in submissions if s.get('verdict') == 'OK'))
            milestone = milestone_value or (solved_count // 100 * 100)
            title = "💪 CODING MILESTONE! 💪"
            subtitle = f"{target_handle} solved {milestone}+ problems!"
            description = f"Total Solved: {solved_count}\nRating: {current_rating}"
            
        else:  # contest_milestone
            contest_count = len(rating_changes) if rating_changes else 0
            title = "🏆 CONTEST WARRIOR! 🏆"
            subtitle = f"{target_handle} participated in {contest_count}+ contests!"
            description = f"Contests: {contest_count}\nRating: {current_rating}"
        
        # Draw achievement content
        # Title
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) // 2, 100), title, font=title_font, fill=(255, 255, 255))
        
        # Subtitle
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(((width - subtitle_width) // 2, 180), subtitle, font=subtitle_font, fill=(255, 215, 0))
        
        # Description
        desc_lines = description.split('\n')
        y_pos = 280
        for line in desc_lines:
            line_bbox = draw.textbbox((0, 0), line, font=text_font)
            line_width = line_bbox[2] - line_bbox[0]
            draw.text(((width - line_width) // 2, y_pos), line, font=text_font, fill=(200, 200, 200))
            y_pos += 35
        
        # Add decorative stars
        star_positions = [(100, 150), (700, 150), (150, 450), (650, 450), (400, 400)]
        for x, y in star_positions:
            draw.regular_polygon((x, y, 20), 5, fill=(255, 215, 0))
        
        # Footer
        footer_text = f"Achievement unlocked on {datetime.now().strftime('%B %d, %Y')}"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=text_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        draw.text(((width - footer_width) // 2, height - 50), footer_text, font=text_font, fill=(150, 150, 150))
        
        # Convert to base64
        image_base64 = _image_to_base64(image)
        
        response_text = f"🎊 **Achievement Card Created!**\n\n"
        response_text += f"Congratulations {target_handle} on this milestone! 🎉\n"
        response_text += f"Perfect for sharing your success! 🚀"
        
        return _create_image_response(response_text, image_base64)
        
    except Exception as e:
        raise McpError(ErrorData(code=500, message=f"❌ Error generating achievement card: {str(e)}"))


# --- TOOL: Generate Comparison Card ---

ComparisonCardDesc = RichToolDescription(
    description="Creates a side-by-side comparison card for multiple Codeforces users showing their stats and ratings.",
    use_when="User asks to 'compare profiles', 'versus card', 'comparison image', or 'compare with friend'.",
    side_effects="Makes network requests to Codeforces API for multiple users and generates a comparison image."
)

@mcp.tool(description=ComparisonCardDesc.model_dump_json())
async def generate_comparison_card(
    handles: Annotated[List[str], Field(description="List of 2-4 Codeforces handles to compare.")],
    show_graph: Annotated[bool, Field(description="Whether to include rating graphs for each user.")] = True
) -> List[TextContent | ImageContent]:
    
    if not handles or len(handles) < 2:
        raise McpError(ErrorData(code=400, message="Please provide at least 2 handles for comparison."))
    
    if len(handles) > 4:
        handles = handles[:4]  # Limit to 4 for layout reasons
    
    try:
        # Fetch data for all users
        user_data = []
        for handle in handles:
            user_info_list, rating_changes, submissions = await asyncio.gather(
                CodeforcesAPI.get_user_info([handle]),
                CodeforcesAPI.get_user_rating_changes(handle),
                CodeforcesAPI.get_user_status(handle, count=1000)
            )
            
            if user_info_list:
                solved_count = len(set(f"{s['problem'].get('contestId')}-{s['problem'].get('index')}" 
                                     for s in submissions if s.get('verdict') == 'OK'))
                user_data.append({
                    'handle': handle,
                    'info': user_info_list[0],
                    'rating_changes': rating_changes,
                    'solved_count': solved_count
                })
        
        if not user_data:
            raise McpError(ErrorData(code=404, message="No valid users found for comparison."))
        
        # Create comparison layout
        user_count = len(user_data)
        if user_count == 2:
            width, height = 900, 500
            cols, rows = 2, 1
        elif user_count == 3:
            width, height = 900, 700
            cols, rows = 2, 2  # 2 top, 1 bottom center
        else:  # 4 users
            width, height = 900, 700
            cols, rows = 2, 2
        
        # Create base image
        image = Image.new('RGB', (width, height), (240, 240, 250))
        draw = ImageDraw.Draw(image)
        
        # Fonts
        title_font = _get_default_font(32)
        header_font = _get_default_font(20)
        text_font = _get_default_font(16)
        
        # Title
        title_text = f"Profile Comparison"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) // 2, 20), title_text, font=title_font, fill=(50, 50, 50))
        
        # Calculate card dimensions
        card_width = (width - 60) // cols
        card_height = (height - 100) // rows
        
        # Draw each user's card
        for i, user in enumerate(user_data):
            if user_count == 3 and i == 2:
                # Center the third card
                col = 0
                row = 1
                x = (width - card_width) // 2
            else:
                col = i % cols
                row = i // cols
                x = 30 + col * (card_width + 10)
            
            y = 80 + row * (card_height + 10)
            
            # Card background
            rank = user['info'].get('rank', 'Unrated')
            card_color = _get_rank_color(rank)
            lighter_color = tuple(min(255, c + 50) for c in card_color)
            
            draw.rectangle([x, y, x + card_width, y + card_height], 
                          fill=(250, 250, 250), outline=card_color, width=3)
            
            # Header with handle and rank
            header_y = y + 15
            draw.text((x + 15, header_y), user['handle'], font=header_font, fill=card_color)
            draw.text((x + 15, header_y + 30), rank.title(), font=text_font, fill=(100, 100, 100))
            
            # Stats
            stats_y = header_y + 70
            current_rating = user['info'].get('rating', 0)
            max_rating = user['info'].get('maxRating', current_rating)
            
            draw.text((x + 15, stats_y), f"Rating: {current_rating}", font=text_font, fill=(50, 50, 50))
            if max_rating != current_rating:
                draw.text((x + 15, stats_y + 25), f"Max: {max_rating}", font=text_font, fill=(100, 100, 100))
            
            draw.text((x + 15, stats_y + 50), f"Solved: {user['solved_count']}", font=text_font, fill=(50, 50, 50))
            
            # Mini rating graph if enabled and data available
            if show_graph and user['rating_changes'] and len(user['rating_changes']) > 1:
                graph_x = x + 15
                graph_y = stats_y + 85
                graph_width = card_width - 30
                graph_height = 80
                
                # Graph background
                draw.rectangle([graph_x, graph_y, graph_x + graph_width, graph_y + graph_height], 
                              fill=(255, 255, 255), outline=card_color, width=1)
                
                # Plot rating changes
                sorted_changes = sorted(user['rating_changes'], key=lambda x: x['ratingUpdateTimeSeconds'])
                ratings = [rc['newRating'] for rc in sorted_changes]
                
                if len(ratings) > 1:
                    min_rating = min(ratings)
                    max_rating_graph = max(ratings)
                    rating_range = max_rating_graph - min_rating if max_rating_graph != min_rating else 1
                    
                    points = []
                    for j, rating in enumerate(ratings):
                        px = graph_x + 5 + (j * (graph_width - 10)) // (len(ratings) - 1)
                        py = graph_y + graph_height - 5 - int(((rating - min_rating) / rating_range) * (graph_height - 10))
                        points.append((px, py))
                    
                    # Draw lines
                    for j in range(len(points) - 1):
                        draw.line([points[j], points[j + 1]], fill=card_color, width=2)
        
        # Convert to base64
        image_base64 = _image_to_base64(image)
        
        response_text = f"⚔️ **Profile Comparison Generated!**\n\n"
        response_text += f"Comparing {len(user_data)} profiles:\n"
        for user in user_data:
            rating = user['info'].get('rating', 0)
            rank = user['info'].get('rank', 'Unrated')
            response_text += f"• {user['handle']}: {rating} ({rank.title()})\n"
        response_text += "\nGreat for friendly competition! 🏆"
        
        return _create_image_response(response_text, image_base64)
        
    except Exception as e:
        raise McpError(ErrorData(code=500, message=f"❌ Error generating comparison card: {str(e)}"))