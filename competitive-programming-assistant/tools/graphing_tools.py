import asyncio
import base64
import io
from collections import Counter, defaultdict
from datetime import datetime
from typing import Annotated, List, Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pydantic import Field
from mcp import ErrorData, McpError
from mcp.types import TextContent, ImageContent

import config
from api_clients.codeforces import CodeforcesAPI
from tools.models import RichToolDescription
from mcp_instance import mcp

# --- Helper Functions ---
def _plot_to_base64() -> str:
    """Saves the current matplotlib plot to a base64 encoded string."""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close() # Close the figure to free memory
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def _create_image_response(text: str, image_base64: str) -> List[TextContent | ImageContent]:
    """Creates the standard MCP response format for an image using proper MCP types."""
    return [
        TextContent(type="text", text=text), 
        ImageContent(type="image", mimeType="image/png", data=image_base64)
    ]


# --- TOOL: Plot Rating Graph (Enhanced) ---
PlotRatingGraphDesc = RichToolDescription(
    description="Shows a line graph of Codeforces rating over time for one or more users. Supports comparison and clear visual progress.",
    use_when="User wants visual analysis of rating progression, performance comparison, or uses phrases like 'rating graph', 'rating plot', 'show my progress visually', 'compare ratings', 'plot my rating', 'rating chart', 'visual rating history', 'graph comparison', or 'rating over time'.",
    side_effects="Makes network requests to fetch rating history for all specified users, then generates and returns a high-quality PNG image. Processing time depends on number of users and their contest history, typically 3-7 seconds."
)
@mcp.tool(description=PlotRatingGraphDesc.model_dump_json())
async def plot_rating_graph(
    handles: Annotated[Optional[List[str]], Field(description="A list of Codeforces handles.")] = None,
    handle: Annotated[Optional[str], Field(description="A single Codeforces handle (alternative to handles).")] = None
) -> List[TextContent | ImageContent]:
    # Handle both singular and plural parameter names for compatibility
    if handle and not handles:
        target_handles = [handle]
    elif handles:
        target_handles = handles
    elif config.DEFAULT_HANDLE:
        target_handles = [config.DEFAULT_HANDLE]
    else:
        raise McpError(ErrorData(code=400, message="Please specify at least one handle (use 'handle' or 'handles' parameter)."))

    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(12, 7))

        all_changes = await asyncio.gather(*[CodeforcesAPI.get_user_rating_changes(h) for h in target_handles])

        if all(not changes for changes in all_changes):
             raise McpError(ErrorData(code=404, message=f"😕 No rating changes found for any of the specified users."))

        for i, (handle, changes) in enumerate(zip(target_handles, all_changes)):
            if not changes:
                print(f"No rating changes for {handle}, skipping.")
                continue

            changes.sort(key=lambda x: x['ratingUpdateTimeSeconds'])
            ratings = [rc['newRating'] for rc in changes]
            times = [datetime.fromtimestamp(rc['ratingUpdateTimeSeconds']) for rc in changes]

            ax.plot(times, ratings, marker='o', linestyle='-', label=handle, markersize=4, linewidth=2)

        ax.set_title("Codeforces Rating History", fontsize=16, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Rating", fontsize=12)
        ax.legend()
        fig.autofmt_xdate()
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()

        image_base64 = _plot_to_base64()
        handles_str = ', '.join(target_handles)
        return _create_image_response(f"Here is the rating graph for {handles_str}:", image_base64)
    except Exception as e:
        plt.close()
        raise McpError(ErrorData(code=500, message=f"❌ Error plotting rating graph: {str(e)}"))


# --- TOOL: Plot Performance Graph ---
PlotPerformanceDesc = RichToolDescription(
    description="Shows contest-by-contest true performance ratings for a user. Highlights skill changes and consistency.",
    use_when="User wants detailed contest analysis, performance consistency evaluation, or uses phrases like 'true performance graph', 'performance rating plot', 'contest performance', 'raw performance', 'actual skill graph', 'performance analysis', or 'show my real performance'.",
    side_effects="Makes network requests to fetch detailed contest data and performs performance calculations. Generates high-quality visualization. Response time typically 2-5 seconds."
)
@mcp.tool(description=PlotPerformanceDesc.model_dump_json())
async def plot_performance_graph(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None,
) -> List[TextContent | ImageContent]:
    target_handle = handle or config.DEFAULT_HANDLE
    if not target_handle:
        raise McpError(ErrorData(code=400, message="Please specify a handle or set DEFAULT_HANDLE."))

    try:
        rating_changes = await CodeforcesAPI.get_user_rating_changes(target_handle)
        if not rating_changes:
            raise McpError(ErrorData(code=404, message=f"😕 No rating changes found for **{target_handle}**. They might be unrated."))

        # Sort chronologically for plotting
        rating_changes.sort(key=lambda x: x['ratingUpdateTimeSeconds'])

        # --- Calculate the "True Performance" Rating for each contest ---
        times = []
        performance_ratings = []
        for rc in rating_changes:
            times.append(datetime.fromtimestamp(rc['ratingUpdateTimeSeconds']))
            delta = rc['newRating'] - rc['oldRating']
            # The formula you provided: performance = old_rating + (delta * 4)
            performance = rc['oldRating'] + (delta * 4)
            performance_ratings.append(performance)
        
        # Current rating for the legend
        current_rating = rating_changes[-1]['newRating'] if rating_changes else 0

        plt.style.use('ggplot') # Use a style similar to the image provided
        fig, ax = plt.subplots(figsize=(12, 7))

        # --- Add the colored background bands for ranks ---
        rank_bands = [
            (0, 1200, '#CCCCCC', 0.5),      # Newbie (Gray)
            (1200, 1400, '#77FF77', 0.5),   # Pupil (Green)
            (1400, 1600, '#77DDBB', 0.5),   # Specialist (Cyan)
            (1600, 1900, '#AAAAFF', 0.5),   # Expert (Blue)
            (1900, 2100, '#FF88FF', 0.5),   # Candidate Master (Violet)
            (2100, 2300, '#FFCC88', 0.5),   # Master (Orange)
        ]
        # Get the max performance to extend the top band
        max_perf = max(performance_ratings) if performance_ratings else 2300
        
        for low, high, color, alpha in rank_bands:
            ax.axhspan(low, high, facecolor=color, alpha=alpha, zorder=0)
        # Add a top band that goes up to the max performance rating
        ax.axhspan(2300, max(2400, max_perf + 100), facecolor='#FFBB55', alpha=0.5, zorder=0)

        # Plot the performance line graph
        ax.plot(times, performance_ratings, color='slateblue', marker='o', 
                markersize=4, markerfacecolor='white', markeredgewidth=0.5,
                linestyle='-', zorder=1, label=f'{target_handle} ({current_rating})')
        
        # Set titles and labels
        ax.set_title(f"Codeforces Performance for {target_handle}", fontsize=16, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Performance Rating", fontsize=12)
        ax.legend(loc='upper left')
        
        fig.autofmt_xdate()
        plt.tight_layout()
        
        image_base64 = _plot_to_base64()
        return _create_image_response(f"Here is the performance graph for {target_handle}:", image_base64)

    except Exception as e:
        plt.close()
        raise McpError(ErrorData(code=500, message=f"❌ Error plotting performance graph: {str(e)}"))


# --- TOOL: Plot Solved Rating Distribution ---
PlotHistogramDesc = RichToolDescription(
    description="Shows a bar chart of solved problems by rating range. Reveals strengths and gaps in practice.",
    use_when="User wants visual analysis of their problem-solving distribution, skill assessment, or uses phrases like 'rating distribution plot', 'graph of solved problems', 'visual histogram', 'show my skill distribution', 'problem rating chart', 'solved problems graph', or 'rating breakdown chart'.",
    side_effects="Makes network requests to fetch comprehensive submission history and performs statistical analysis. Generates a high-quality histogram image. Response time typically 3-6 seconds depending on submission volume."
)
@mcp.tool(description=PlotHistogramDesc.model_dump_json())
async def plot_solved_rating_distribution(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None,
) -> List[TextContent | ImageContent]:
    target_handle = handle or config.DEFAULT_HANDLE
    if not target_handle or target_handle.strip() == "":
        raise McpError(ErrorData(code=400, message="Please specify a handle or set DEFAULT_HANDLE."))
    try:
        submissions = await CodeforcesAPI.get_user_status(target_handle, count=5000)

        solved_ratings = []
        seen_problems = set()
        for sub in submissions:
            if sub.get('verdict') == 'OK':
                problem = sub['problem']
                problem_id = f"{problem.get('contestId')}-{problem.get('index')}"
                if 'rating' in problem and problem_id not in seen_problems:
                    solved_ratings.append(problem['rating'])
                    seen_problems.add(problem_id)

        if not solved_ratings:
            raise McpError(ErrorData(code=404, message=f"😕 No rated problems solved by *{target_handle}*."))

        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.histplot(solved_ratings, binwidth=100, kde=True, ax=ax, color='dodgerblue', edgecolor='black')
        ax.set_title(f"Solved Problem Rating Distribution for {target_handle}", fontsize=16, fontweight='bold')
        ax.set_xlabel("Problem Rating", fontsize=12)
        ax.set_ylabel("Number of Problems Solved", fontsize=12)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(200))
        plt.tight_layout()

        image_base64 = _plot_to_base64()
        return _create_image_response(f"Here's a histogram of solved problem ratings for {target_handle}:", image_base64)
    except Exception as e:
        plt.close()
        raise McpError(ErrorData(code=500, message=f"❌ Error plotting rating distribution: {str(e)}"))


# --- TOOL: Plot Verdict Distribution ---
PlotVerdictsDesc = RichToolDescription(
    description="Shows a pie chart of submission verdicts (Accepted, Wrong Answer, etc.) for a user. Useful for accuracy and error analysis.",
    use_when="User wants to analyze submission patterns, accuracy rates, or uses phrases like 'verdict chart', 'submission summary', 'pie chart of results', 'how accurate am I', 'submission stats', 'verdict distribution', 'success rate', or 'error analysis'.",
    side_effects="Makes network requests to fetch extensive submission history and calculates verdict statistics. Generates a colorful pie chart with percentages. Response time typically 2-4 seconds."
)
@mcp.tool(description=PlotVerdictsDesc.model_dump_json())
async def plot_verdict_distribution(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None
) -> List[TextContent | ImageContent]:
    target_handle = handle or config.DEFAULT_HANDLE
    if not target_handle or target_handle.strip() == "":
        raise McpError(ErrorData(code=400, message="Please specify a handle or set DEFAULT_HANDLE."))

    try:
        submissions = await CodeforcesAPI.get_user_status(target_handle, count=5000)
        if not submissions:
            raise McpError(ErrorData(code=404, message=f"No submissions found for {target_handle}."))

        verdict_counts = Counter(sub.get('verdict', 'UNKNOWN') for sub in submissions)
        main_verdicts = {'OK', 'WRONG_ANSWER', 'TIME_LIMIT_EXCEEDED', 'MEMORY_LIMIT_EXCEEDED', 'RUNTIME_ERROR', 'COMPILATION_ERROR'}
        verdict_data = Counter()
        other_count = 0
        for verdict, count in verdict_counts.items():
            if verdict in main_verdicts:
                verdict_data[verdict] = count
            else:
                other_count += count
        if other_count > 0:
            verdict_data['OTHER'] = other_count

        labels = list(verdict_data.keys())
        sizes = list(verdict_data.values())

        plt.style.use('seaborn-v0_8-deep')
        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, pctdistance=0.85)
        plt.setp(autotexts, size=10, weight="bold", color="white")
        ax.axis('equal')
        ax.set_title(f'Submission Verdicts for {target_handle}', fontsize=16, fontweight='bold')

        image_base64 = _plot_to_base64()
        return _create_image_response(f"Here is the verdict distribution for {target_handle}:", image_base64)
    except Exception as e:
        plt.close()
        raise McpError(ErrorData(code=500, message=f"❌ Error plotting verdicts: {str(e)}"))

# --- TOOL: Plot Tag Distribution ---
PlotTagsDesc = RichToolDescription(
    description="Shows a bar chart of most solved problem tags/topics. Reveals strengths and areas to improve.",
    use_when="User wants to analyze their algorithmic strengths, plan study topics, or uses phrases like 'tag distribution', 'my strengths', 'topic analysis', 'what algorithms do I know', 'algorithmic skills', 'problem categories', 'topic strengths', 'weaknesses', or 'what tags I solve most'.",
    side_effects="Makes network requests to fetch user's solved problems with tag information and performs frequency analysis. Generates a professional bar chart. Response time typically 3-5 seconds."
)
@mcp.tool(description=PlotTagsDesc.model_dump_json())
async def plot_tag_distribution(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None,
    count: Annotated[int, Field(description="Number of top tags to show.")] = 15
) -> List[TextContent | ImageContent]:
    # Implementation omitted for brevity - copy from your original script
    return "Tag distribution plot logic goes here."

# --- TOOL: Plot Language Distribution ---
PlotLangsDesc = RichToolDescription(
    description="Shows a pie chart of programming languages used in submissions. Useful for language preference analysis.",
    use_when="User wants to analyze their programming language usage, coding versatility, or uses phrases like 'language chart', 'languages used', 'programming language distribution', 'what languages do I use', 'language preferences', 'coding languages', or 'language stats'.",
    side_effects="Makes network requests to fetch submission history with language information and calculates usage statistics. Generates a clear pie chart visualization. Response time typically 2-4 seconds."
)
@mcp.tool(description=PlotLangsDesc.model_dump_json())
async def plot_language_distribution(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None
) -> List[TextContent | ImageContent]:
    # Implementation omitted for brevity - copy from your original script
    return "Language distribution plot logic goes here."