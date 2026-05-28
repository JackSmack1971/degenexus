import math
import requests

from src.core.settings import Settings

BASE = "https://openrouter.ai/api/v1"
_settings = Settings()
API_KEY = _settings.openrouter_api_key.get_secret_value() if _settings.openrouter_api_key else None

def _get(path: str):
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    r = requests.get(f"{BASE}{path}", headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def _is_zero(x):
    try:
        return x is None or math.isclose(float(x), 0.0, rel_tol=0, abs_tol=0)
    except Exception:
        return False

def list_free_active_models():
    out = []
    models = _get("/models")["data"]
    for m in models:
        p = m.get("pricing", {}) or {}
        if not (_is_zero(p.get("prompt")) and _is_zero(p.get("completion")) and _is_zero(p.get("request"))):
            continue
        slug = m.get("canonical_slug") or m["id"]
        ep = _get(f"/models/{slug}/endpoints")["data"]["endpoints"]
        active_eps = [e for e in ep if str(e.get("status", "")).lower() == "online" or (e.get("uptime_last_30m") or 0) > 0]
        if active_eps:
            out.append(slug)
    return out

if __name__ == "__main__":
    free_active = list_free_active_models()
    print(f"Free & active models: {len(free_active)}")
    for m in free_active:
        print(m)
