"""
Shared async Ollama HTTP client with per-event-loop concurrency limiting.
Prevents parallel section extractors from saturating single-slot local Ollama
and timing out while queued.
"""

import asyncio
import weakref
from typing import Any, Dict
import httpx


_loop_semaphores: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Semaphore]" = (
    weakref.WeakKeyDictionary()
)


def get_ollama_semaphore() -> asyncio.Semaphore:
    """Returns a concurrency-1 semaphore bound to the current running event loop."""
    loop = asyncio.get_running_loop()
    sem = _loop_semaphores.get(loop)
    if sem is None:
        sem = asyncio.Semaphore(1)
        _loop_semaphores[loop] = sem
    return sem


async def post_ollama_chat(
    base_url: str,
    payload: Dict[str, Any],
    timeout: float,
) -> httpx.Response:
    """
    Sends a POST /api/chat request to Ollama under a concurrency-1 semaphore
    so the httpx timeout only measures active inference rather than queue wait.
    """
    semaphore = get_ollama_semaphore()
    async with semaphore:
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(
                f"{base_url.rstrip('/')}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
