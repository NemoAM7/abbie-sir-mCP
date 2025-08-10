import config
from fastmcp import FastMCP
from mcp.server.auth.provider import AccessToken
# Using the deprecated but working bearer auth for compatibility with starter kit
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="fastmcp.server.auth.providers.bearer")
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair

# Using BearerAuthProvider like in the starter kit examples
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        key = RSAKeyPair.generate()
        super().__init__(public_key=key.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="puch-client",
                scopes=["*"],
                expires_at=None,
            )
        return None

# The single, central MCP instance for the entire application - following starter kit pattern
mcp = FastMCP(
    "Ultimate Competitive Programming Assistant v5.5",
    auth=SimpleBearerAuthProvider(config.TOKEN),
)