"""
AI-Assisted Extractor for Education Analysis
Phase 3 | Feature 14: Education Analysis
Leverages local Ollama LLM to extract structured academic records.
"""

import json
import logging
from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings
from app.services.ollama_client import post_ollama_chat

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an accurate, strict academic information extraction engine.
Your task is to extract all education qualifications and degrees from the provided resume text.

CRITICAL RULES:
1. ONLY extract academic qualifications explicitly mentioned.
2. DO NOT fabricate or guess universities, degrees, or grades.
3. If an education entry has missing fields, set them to null.
4. Support multiple education entries (e.g., Master's, Bachelor's, High School).
5. Extract exact grades and scales (CGPA, GPA, or percentage) without converting between them.
6. Return ONLY a valid JSON object matching this exact schema:
{
  "education": [
    {
      "degree": string or null,
      "institution": string or null,
      "location": string or null,
      "field_of_study": string or null,
      "specialization": string or null,
      "start_date": string or null,
      "end_date": string or null,
      "graduation_status": "completed" | "ongoing" | "expected" | "discontinued",
      "grade": {
        "value": number or null,
        "type": "CGPA" | "GPA" | "Percentage" | "Classification" | null,
        "scale": number or null,
        "raw_grade": string or null
      } or null,
      "achievements": string[],
      "coursework": string[],
      "honors": string[],
      "source_evidence": string[]
    }
  ]
}
"""


class EducationAIExtractor:
    """Interacts with local Ollama runtime to parse multiple academic records."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def extract_education_entries(
        self, education_text: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Sends education text to local Ollama.
        Returns parsed list of education dictionaries or None on failure/timeout.
        """
        if not education_text or not education_text.strip():
            return None

        # Bound input text to prevent prompt injection and token bloat
        sample_text = education_text[:3000].strip()

        user_content = (
            f"Extract all academic qualifications from this education text:\n\n"
            f"<education_text>\n{sample_text}\n</education_text>"
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
            response = await post_ollama_chat(
                base_url=self.base_url,
                payload=payload,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.info("Ollama education extraction HTTP %d, falling back to deterministic", response.status_code)
                return None

            result_json = response.json()
            content = result_json.get("message", {}).get("content", "")
            if not content:
                return None

            parsed = json.loads(content)
            if isinstance(parsed, dict) and "education" in parsed and isinstance(parsed["education"], list):
                return parsed["education"]

        except httpx.ConnectError:
            logger.info("Local Ollama service not reachable, using deterministic education fallback")
        except httpx.TimeoutException:
            logger.info("Ollama request timed out, using deterministic education fallback")
        except Exception as exc:
            logger.warning("Error during Ollama education extraction: %s", type(exc).__name__)

        return None


education_ai_extractor = EducationAIExtractor()
