import json, os, time
from typing import Any, Optional

class SimpleTTLCache:
    def __init__(self, cache_dir: str = ".cache", ttl_seconds: int = 900):
        self.cache_dir = cache_dir
        self.ttl = ttl_seconds
        os.makedirs(cache_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get(self, key: str) -> Optional[Any]:
        p = self._path(key)
        if not os.path.exists(p):
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if time.time() - payload.get("_t", 0) > self.ttl:
                return None
            return payload.get("data")
        except Exception:
            return None

    def set(self, key: str, data: Any):
        p = self._path(key)
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"_t": time.time(), "data": data}, f, ensure_ascii=False, indent=2)
