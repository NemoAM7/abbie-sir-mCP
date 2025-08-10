from typing import Optional
from mcp import ErrorData, McpError
from .base_client import ApiClient

class LeetCodeAPI(ApiClient):
    BASE_URL = "https://leetcode.com/graphql"
    
    @classmethod
    async def _send_query(cls, query: str, variables: Optional[dict] = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = await cls.post(cls.BASE_URL, json=payload)
        data = resp.json()
        if "errors" in data:
            raise McpError(ErrorData(code=400, message=f"LeetCode API Error: {data['errors']}"))
        return data.get("data", {})

    @classmethod
    async def get_daily_problem(cls) -> dict:
        query = """
        query questionOfToday {
            activeDailyCodingChallengeQuestion {
                date
                link
                question {
                    difficulty
                    title
                    titleSlug
                    content
                    topicTags { name }
                }
            }
        }
        """
        return await cls._send_query(query)