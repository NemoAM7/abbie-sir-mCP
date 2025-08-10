from datetime import datetime
from typing import List
from .base_client import ApiClient
import config

class CListAPI(ApiClient):
    BASE_URL = "https://clist.by/api/v4/contest/"
    
    PLATFORM_MAPPING = {
        "codeforces": "codeforces.com",
        "leetcode": "leetcode.com",
        "codechef": "codechef.com",
        "atcoder": "atcoder.jp",
        "topcoder": "topcoder.com",
        "codingninjas": "codingninjas.com/codestudio",
    }

    @classmethod
    async def get_upcoming_contests(cls, platforms: List[str]) -> List[dict]:
        now_utc = datetime.utcnow().isoformat()
        resource_names = [cls.PLATFORM_MAPPING[p] for p in platforms if p in cls.PLATFORM_MAPPING]
        if not resource_names:
            return []
            
        params = {"start__gt": now_utc, "order_by": "start", "resource__in": ",".join(resource_names)}
        headers = {"Authorization": f"ApiKey {config.CLIST_API_KEY}"}
        
        resp = await cls.get(cls.BASE_URL, params=params, headers=headers)
        return resp.json().get("objects", [])