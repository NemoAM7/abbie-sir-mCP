from typing import List, Optional
from mcp import ErrorData, McpError
from .base_client import ApiClient

class CodeforcesAPI(ApiClient):
    BASE_URL = "https://codeforces.com/api"
    
    @classmethod
    async def query(cls, endpoint: str, params: Optional[dict] = None) -> dict:
        resp = await cls.get(f"{cls.BASE_URL}/{endpoint}", params=params)
        data = resp.json()
        if data.get("status") != "OK":
            raise McpError(ErrorData(code=400, message=f"Codeforces Error: {data.get('comment', 'Unknown error')}"))
        return data.get("result", {})
    
    @classmethod
    async def get_user_info(cls, handles: List[str]) -> List[dict]:
        return await cls.query("user.info", {"handles": ";".join(handles)})
    
    @classmethod
    async def get_user_status(cls, handle: str, count: int = 1000) -> List[dict]:
        return await cls.query("user.status", {"handle": handle, "from": 1, "count": count})

    @classmethod
    async def get_user_rating_changes(cls, handle: str) -> List[dict]:
        return await cls.query("user.rating", {"handle": handle})

    @classmethod
    async def get_problemset(cls, tags: Optional[List[str]] = None) -> dict:
        params = {"tags": ";".join(tags)} if tags else {}
        return await cls.query("problemset.problems", params)