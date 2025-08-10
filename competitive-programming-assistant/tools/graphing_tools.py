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
    description="Generates a plot of rating history for one or more Codeforces users.",
    use_when="User asks for a 'rating graph', 'rating plot', or to 'compare ratings' visually.",
    side_effects="Makes network requests to the Codeforces API and generates an image."
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


# --- TOOL: Plot Solved Rating Distribution ---
PlotHistogramDesc = RichToolDescription(
    description="Displays a graphical histogram of solved problem ratings for a user.",
    use_when="User asks for a 'rating distribution plot', 'graph of solved problems', or a visual histogram.",
    side_effects="Makes a network request for the user's submission history and generates an image."
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
    description="Generates a pie chart of a user's submission verdicts.",
    use_when="User asks for a 'verdict chart', 'submission summary', or 'pie chart of results'.",
    side_effects="Makes a network request for user submissions and generates an image."
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
    description="Generates a bar chart of a user's most solved problem tags.",
    use_when="User asks for 'tag distribution', 'strengths', 'weaknesses', or 'what tags I solve'.",
    side_effects="Makes a network request for user submissions and generates an image."
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
    description="Generates a pie chart of the programming languages a user submits with.",
    use_when="User asks for a 'language chart', 'languages used', or 'programming language distribution'.",
    side_effects="Makes a network request for user submissions and generates an image."
)
@mcp.tool(description=PlotLangsDesc.model_dump_json())
async def plot_language_distribution(
    handle: Annotated[Optional[str], Field(description="The user's Codeforces handle. Defaults to your configured handle.")] = None
) -> List[TextContent | ImageContent]:
    # Implementation omitted for brevity - copy from your original script
    return "Language distribution plot logic goes here."