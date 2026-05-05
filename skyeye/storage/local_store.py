from pathlib import Path


class LocalObjectStore:
    """Filesystem-backed object store using local:// URIs."""

    scheme = "local://"

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, key: str, content: bytes, content_type: str) -> str:
        del content_type
        safe_key = self._safe_key(key)
        target = self.root / safe_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return f"{self.scheme}{safe_key.as_posix()}"

    def resolve_uri(self, uri: str) -> Path:
        if not uri.startswith(self.scheme):
            raise ValueError(f"Unsupported local object URI: {uri}")
        safe_key = self._safe_key(uri[len(self.scheme):])
        return self.root / safe_key

    def delete(self, uri: str) -> None:
        path = self.resolve_uri(uri)
        if path.exists():
            path.unlink()

    def _safe_key(self, key: str) -> Path:
        raw = Path(key.replace("\\", "/"))
        if raw.is_absolute() or any(part == ".." for part in raw.parts):
            raise ValueError(f"Unsafe object key: {key}")

        normalized = Path(*[part for part in raw.parts if part not in ("", ".")])
        resolved = (self.root / normalized).resolve()
        if self.root not in (resolved, *resolved.parents):
            raise ValueError(f"Object key escapes storage root: {key}")
        return normalized
