"""
AI-Assisted Certifications and Achievements Extractor
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Interacts with local Ollama LLM for semantic extraction of complex accomplishments,
honors, and non-standard certification descriptions.
"""

import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings
from app.services.ollama_client import post_ollama_chat

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a strict, precise Certifications & Achievements Intelligence Extraction Engine for a career analytics platform.
Your task is to analyze candidate accomplishment text and extract structured certification and achievement details.

CRITICAL RULES:
1. Extract ONLY facts explicitly stated in the text.
2. NEVER invent certification names, credential IDs, verification URLs, or expiry dates.
3. NEVER elevate a hackathon or competition "Participant", "Attendee", or "Volunteer" to a "Winner" or ranked award.
4. For certifications, classify category into: "technical", "professional", "cloud", "ai_ml", "programming", "data_science", "security", "project_management", "course", "training", "other".
5. For achievements, classify category into: "hackathon", "competition", "academic", "scholarship", "research", "publication", "professional", "leadership", "technical", "community", "volunteer", "other".
6. Return ONLY a valid JSON object matching this schema:
{
  "is_certification": boolean,
  "title": string,
  "organization_or_issuer": string or null,
  "category": string,
  "rank_or_position": string or null,
  "issue_or_event_date": string or null,
  "credential_id": string or null,
  "status": string or null,
  "team_size": number or null,
  "candidate_role": string or null
}
"""


class CertificationsAIExtractor:
    """Ollama AI service for semantic certification and achievement analysis."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def analyze_accomplishment_text(
        self,
        text: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Sends accomplishment block to local Ollama.
        Returns parsed narrative details or None if offline or error.
        """
        if not text or not text.strip():
            return None

        sample_text = text[:1500].strip()
        user_content = f"Extract structured facts from this resume accomplishment entry:\n\n<accomplishment_text>\n{sample_text}\n</accomplishment_text>"

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
            response = await post_ollama_chat(
                base_url=self.base_url,
                payload=payload,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.info("Ollama certifications extraction returned status %s", response.status_code)
                return None

            data = response.json()
            message_content = data.get("message", {}).get("content", "")
            if not message_content:
                return None

            parsed = json.loads(message_content)
            if isinstance(parsed, dict):
                return parsed
            return None
        except Exception as exc:
            logger.info("Ollama certifications extraction offline/unavailable: %s", exc)
            return None


certifications_ai_extractor = CertificationsAIExtractor()
