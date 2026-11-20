"""
AI-Assisted Extractor for Experience Analysis
Phase 3 | Feature 15: Experience Analysis
Leverages local Ollama LLM to extract structured professional experience records.
"""

import json
import logging
from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an accurate, strict professional experience information extraction engine.
Your task is to extract all professional work experience and employment records from the provided resume text.

CRITICAL RULES:
1. ONLY extract professional experience (jobs, internships, freelance, contract, research roles) explicitly mentioned.
2. DO NOT classify academic student projects or extracurriculars as employment unless explicitly stated as a job/internship.
3. If an entry has missing fields (like location or company), set them to null.
4. Support multiple experience entries in chronological order.
5. Extract exact dates normalized to YYYY-MM or YYYY. If current, set is_current=true and end_date=null.
6. Extract responsibilities, technical contributions, technologies used, achievements, and quantified measurable impacts without inventing numbers or percentages.
7. Return ONLY a valid JSON object matching this exact schema:
{
  "experience": [
    {
      "company": string or null,
      "job_title": string or null,
      "employment_type": "full_time" | "part_time" | "internship" | "freelance" | "contract" | "apprenticeship" | "research" | "volunteer" | "other",
      "location": string or null,
      "start_date": string or null,
      "end_date": string or null,
      "is_current": boolean,
      "responsibilities": string[],
      "technical_contributions": string[],
      "technologies": string[],
      "achievements": string[],
      "measurable_impact": string[],
      "source_evidence": string[]
    }
  ]
}
"""


class ExperienceAIExtractor:
    """Interacts with local Ollama runtime to parse work experience records."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def extract_experience_entries(
        self, experience_text: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Sends experience text to local Ollama.
        Returns parsed list of experience dictionaries or None on failure/timeout.
        """
        if not experience_text or not experience_text.strip():
            return None

        sample_text = experience_text[:3500].strip()

        user_content = (
            f"Extract all professional experience entries from this text:\n\n"
            f"<experience_text>\n{sample_text}\n</experience_text>"
        )

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
                    headers={"Content-Type": "application/json"},
                )

            if response.status_code != 200:
                logger.warning(
                    "Ollama experience extraction returned status %s: %s",
                    response.status_code,
                    response.text[:200],
                )
                return None

            data = response.json()
            message_content = data.get("message", {}).get("content", "")
            if not message_content:
                return None

            parsed = json.loads(message_content)
            if isinstance(parsed, dict) and "experience" in parsed and isinstance(parsed["experience"], list):
                return parsed["experience"]
            elif isinstance(parsed, list):
                return parsed
            return None

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.info("Ollama unavailable or timed out for experience: %s", exc)
            return None
        except Exception as exc:
            logger.warning("Error during AI experience extraction: %s", exc)
            return None


experience_ai_extractor = ExperienceAIExtractor()
