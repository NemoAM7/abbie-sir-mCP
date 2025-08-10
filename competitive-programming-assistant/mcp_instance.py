import config
from fastmcp import FastMCP
from mcp.server.auth.provider import AccessToken
# This import path is updated to fix the DeprecationWarning
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair

# Using JWTVerifier to be future-proof and fix the deprecation warning.
# This class is essentially the same as the old BearerAuthProvider.
class SimpleJWTAuthProvider(JWTVerifier):
    def __init__(self, token: str):
        key = RSAKeyPair.generate()
        super().__init__(public_key=key.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        return AccessToken(token=token, client_id="puch-client", scopes=["*"]) if token == self.token else None

# The single, central MCP instance for the entire application
mcp = FastMCP(
    "Ultimate Competitive Programming Assistant v5.5",
    auth=SimpleJWTAuthProvider(config.TOKEN)
)