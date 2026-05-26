"""Thin wrapper around the Pexels Photo Search API.

The frontend asks the backend for a food picture URL — the backend (this
module) talks to Pexels with the secret API key from ``PEXELS_API_KEY``
and returns just the chosen URL. Keeping the key server-side means we
never have to expose it in the SPA bundle.

Endpoint reference: https://www.pexels.com/api/documentation/#photos-search
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Optional

PEXELS_API_URL = "https://api.pexels.com/v1/search"


def _api_key() -> str:
    """Read the Pexels API key lazily so missing-key errors surface at the
    request — not at process start — and so tests can set the env after import.

    Also strips whitespace and any accidental surrounding quotes that often
    sneak in when copy-pasting into a ``.env`` file.
    """
    raw = os.environ.get("PEXELS_API_KEY", "")
    key = raw.strip().strip('"').strip("'").strip()
    if not key:
        raise RuntimeError(
            "PEXELS_API_KEY is not set. Get a free key at "
            "https://www.pexels.com/api/ and add it to .env."
        )
    return key


# A real User-Agent — some CDNs in front of Pexels reject the default
# `Python-urllib/3.x` with 403 Forbidden before the request even reaches
# the API.
_USER_AGENT = "tcm-ai-assistant/0.1 (+https://github.com/anthropics/claude-code)"


@lru_cache(maxsize=512)
def search_photo_url(query: str, size: str = "medium") -> Optional[str]:
    """Return one Pexels photo URL matching ``query`` (lowercased, trimmed).

    Results are cached in-process so repeated lookups for the same food name
    do not consume your Pexels quota.

    Returns ``None`` if no photo matched. Raises ``RuntimeError`` on
    network / auth errors with the upstream response body included, so the
    caller can surface the real cause (bad key, rate-limited, etc.).
    """
    q = (query or "").strip().lower()
    if not q:
        return None

    url = f"{PEXELS_API_URL}?{urllib.parse.urlencode({'query': q, 'per_page': 1})}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": _api_key(),
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as exc:
        # Read Pexels' own error body so the caller can see the real reason
        # (invalid key vs. rate limited vs. malformed query, …).
        try:
            err_body = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            err_body = ""
        hint = ""
        if exc.code in (401, 403):
            hint = (
                " — most often a bad PEXELS_API_KEY. Verify with:\n"
                "  curl -sS -H \"Authorization: $PEXELS_API_KEY\" "
                "'https://api.pexels.com/v1/search?query=test&per_page=1'"
            )
        raise RuntimeError(
            f"Pexels returned HTTP {exc.code} {exc.reason}.{hint}\n"
            f"Body: {err_body!r}"
        ) from exc

    photos = body.get("photos") or []
    if not photos:
        return None

    src = photos[0].get("src") or {}
    # Prefer the requested size; fall back through smaller sizes so we always
    # return something usable.
    for key in (size, "medium", "small", "tiny", "original"):
        if src.get(key):
            return src[key]
    return None
