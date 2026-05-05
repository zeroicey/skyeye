from pathlib import Path
from typing import Protocol


class ObjectStore(Protocol):
    """Storage boundary for local files today and object storage later."""

    def put_bytes(self, key: str, content: bytes, content_type: str) -> str:
        """Persist bytes under a relative key and return a stable URI."""

    def resolve_uri(self, uri: str) -> Path:
        """Resolve a readable local path for a URI when supported."""

    def delete(self, uri: str) -> None:
        """Delete an object if it exists."""
