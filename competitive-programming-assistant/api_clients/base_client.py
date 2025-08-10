from typing import Optional
import httpx
from mcp import ErrorData, McpError

class ApiClient:
    """A base class for making asynchronous HTTP requests."""
    USER_AGENT = "PuchAI-CompetitiveProgrammingBot/5.5"

    @classmethod
    async def get(cls, url: str, params: Optional[dict] = None, headers: Optional[dict] = None) -> httpx.Response:
        request_headers = {"User-Agent": cls.USER_AGENT}
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params, headers=request_headers, timeout=30.0)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                raise McpError(ErrorData(code=e.response.status_code, message=f"API Error ({e.request.url}): {e.response.text}"))
            except httpx.RequestError as e:
                raise McpError(ErrorData(code=500, message=f"Network connection error: {e!r}"))

    @classmethod
    async def post(cls, url: str, json: Optional[dict] = None, headers: Optional[dict] = None) -> httpx.Response:
        request_headers = {"User-Agent": cls.USER_AGENT}
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=json, headers=request_headers, timeout=30.0)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                raise McpError(ErrorData(code=e.response.status_code, message=f"API Error ({e.request.url}): {e.response.text}"))
            except httpx.RequestError as e:
                raise McpError(ErrorData(code=500, message=f"Network connection error: {e!r}"))