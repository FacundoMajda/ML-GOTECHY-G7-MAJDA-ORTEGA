# src/providers/youtube_utils.py

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import yt_dlp


_FORMAT_CANDIDATES = [
    "(bv*[vcodec!*=av01]+ba/b[vcodec!*=av01])/best[vcodec!*=av01]",
    "best[height<=1080][ext=mp4]/best[height<=1080]/best",
    "bv*+ba/b",
    "best",
]

# ── YouTube URL cache (ttl=1800s = 30min) ──
_youtube_url_cache: dict[str, tuple[str, float]] = {}
_YOUTUBE_CACHE_TTL = 1800


def _get_cookies_opts() -> dict:
    cookies_file = Path("cookies.txt")
    if cookies_file.exists():
        print(f"[DEBUG] _get_cookies_opts: using cookiefile=cookies.txt", flush=True)
        return {"cookiefile": str(cookies_file.resolve())}
    print(f"[DEBUG] _get_cookies_opts: no cookies.txt found, will try without cookies", flush=True)
    return {}


def extract_youtube_info(url: str, *, download: bool = False) -> dict[str, Any]:
    print(f"[DEBUG] extract_youtube_info: ENTRY url={url[:80]}...", flush=True)
    last_error: Exception | None = None
    cookies_opts = _get_cookies_opts()

    for fmt in _FORMAT_CANDIDATES:
        opts = {
            "format": fmt,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "youtube_include_dash_manifest": True,
        }
        opts.update(cookies_opts)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=download)
                has_url = info.get("url") is not None
                print(f"[DEBUG] extract_youtube_info: success with format={fmt} has_url={has_url}", flush=True)
                return info
        except Exception as exc:  # pragma: no cover - depends on remote source
            print(f"[DEBUG] extract_youtube_info: format={fmt} failed: {exc}", flush=True)
            last_error = exc

    raise RuntimeError(
        f"No se pudo resolver un formato reproducible para {url}: {last_error}"
    )


def extract_stream_url(url: str) -> str:
    # Check cache first
    now = time.time()
    cached = _youtube_url_cache.get(url)
    if cached and (now - cached[1]) < _YOUTUBE_CACHE_TTL:
        print(f"[DEBUG] extract_stream_url: cache HIT for {url[:60]}...", flush=True)
        return cached[0]

    print(f"[DEBUG] extract_stream_url: cache MISS for {url[:80]}...", flush=True)
    info = extract_youtube_info(url, download=False)
    direct_url = info.get("url")
    if direct_url:
        _youtube_url_cache[url] = (direct_url, now)
        print(f"[DEBUG] extract_stream_url: returning direct_url", flush=True)
        return direct_url

    requested = info.get("requested_formats") or []
    for fmt in requested:
        if fmt.get("url"):
            _youtube_url_cache[url] = (fmt["url"], now)
            print(f"[DEBUG] extract_stream_url: returning from requested_formats", flush=True)
            return fmt["url"]

    formats = info.get("formats") or []
    for fmt in reversed(formats):
        if fmt.get("acodec") != "none" and fmt.get("vcodec") != "none" and fmt.get("url"):
            _youtube_url_cache[url] = (fmt["url"], now)
            print(f"[DEBUG] extract_stream_url: returning from formats list", flush=True)
            return fmt["url"]

    raise RuntimeError(f"No se encontro stream URL directo para {url}")
