"""
AI-Assisted Extractor for Personal Information
Phase 3 | Feature 13: Personal Information Extraction
Leverages local Ollama LLM to extract full name, first name, last name, and location.
"""

import json
import logging
from typing import Optional, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an accurate, strict resume information extraction engine.
Your task is to extract the candidate's personal identity and location from the resume header text provided.

CRITICAL RULES:
1. ONLY extract information that is explicitly stated.
2. DO NOT hallucinate or infer names from email addresses.
3. DO NOT guess locations from company or university names.
4. If a field is missing, set its value to null.
5. Return ONLY a valid JSON object matching this exact schema:
{
  "full_name": string or null,
  "first_name": string or null,
  "last_name": string or null,
  "location": {
    "city": string or null,
    "state": string or null,
    "country": string or null
  }
}
"""


class AIExtractor:
    """Interacts with local Ollama runtime to parse ambiguous candidate information."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def extract_identity_and_location(
        self, cleaned_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Sends resume header text to local Ollama.
        Returns parsed dictionary or None on timeout/failure.
        """
        if not cleaned_text or not cleaned_text.strip():
            return None

        # Take top 1500 characters of resume text to prevent prompt bloat and injection
        header_sample = cleaned_text[:1500].strip()

        user_content = f"Extract personal information from this resume header:\n\n<resume_header>\n{header_sample}\n</resume_header>"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.0,
                "top_p": 0.1,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                if response.status_code != 200:
                    logger.info(
                        "Ollama request returned HTTP %d, falling back to heuristic",
                        response.status_code,
                    )
                    return None

                result_json = response.json()
                message_content = result_json.get("message", {}).get("content", "")

                if not message_content:
                    return None

                parsed = json.loads(message_content)
                if isinstance(parsed, dict):
                    return parsed

        except httpx.ConnectError:
            logger.info("Local Ollama service not reachable, using heuristic fallback")
        except httpx.TimeoutException:
            logger.info("Ollama request timed out, using heuristic fallback")
        except Exception as exc:
            logger.warning("Error during Ollama personal info extraction: %s", type(exc).__name__)

        return None


ai_extractor = AIExtractor()
