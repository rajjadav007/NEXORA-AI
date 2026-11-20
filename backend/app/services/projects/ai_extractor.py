"""
AI-Assisted Project Intelligence Extractor
Phase 3 | Feature 18: Project Intelligence
Interacts with local Ollama LLM to extract problem statement, proposed solution,
domain, candidate role, and individual vs team contributions.
"""

import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a strict, precise Project Intelligence Extraction Engine for a career analytics platform.
Your task is to analyze candidate project text and extract structured domain, purpose, problem, solution, and candidate role details.

CRITICAL RULES:
1. Extract ONLY facts explicitly stated in the text.
2. If the problem or solution is not explicitly discussed, leave problem_statement or proposed_solution as null.
3. If candidate individual role or contribution is not explicitly stated, set candidate_role="Contributor" and individual_contribution="Specific individual contribution not specified."
4. Do NOT invent team sizes, metrics, percentages, or leadership titles.
5. Identify domain if clear (e.g. "FinTech", "Healthcare", "AI/ML", "E-Commerce", "Developer Tools", "Education", "Other").
6. Classify category into one of: "academic", "personal", "hackathon", "research", "open_source", "internship", "professional", "freelance", "other".
7. Return ONLY a valid JSON object matching this schema:
{
  "problem_statement": string or null,
  "proposed_solution": string or null,
  "domain": string or null,
  "candidate_role": string or null,
  "individual_contribution": string or null,
  "project_category": string or null
}
"""


class ProjectAIExtractor:
    """Ollama AI service for semantic project narrative extraction."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def analyze_project_narrative(
        self,
        project_text: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Sends project block to local Ollama.
        Returns parsed narrative details or None if offline/error.
        """
        if not project_text or not project_text.strip():
            return None

        sample_text = project_text[:2000].strip()
        user_content = f"Extract structured narrative from this project description:\n\n<project_text>\n{sample_text}\n</project_text>"

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
                logger.info("Ollama project extraction returned status %s", response.status_code)
                return None

            data = response.json()
            message_content = data.get("message", {}).get("content", "")
            if not message_content:
                return None

            parsed = json.loads(message_content)
            if isinstance(parsed, dict):
                return parsed
            return None

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.info("Ollama unavailable for project analysis (%s). Graceful fallback.", exc)
            return None
        except Exception as exc:
            logger.warning("Error during AI project extraction: %s", exc)
            return None


project_ai_extractor = ProjectAIExtractor()
