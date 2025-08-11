from pydantic import BaseModel

class RichToolDescription(BaseModel):
    """
    Enhanced tool description model that provides comprehensive information
    about each tool's functionality, usage scenarios, and performance characteristics.
    """
    description: str  # Detailed explanation of what the tool does and its capabilities
    use_when: str     # Specific scenarios, user phrases, and trigger conditions
    side_effects: str | None = None  # Performance info, API calls, response times, etc.