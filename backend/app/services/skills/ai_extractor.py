"""
AI-Assisted Skill Disambiguation and Suggestion Service
Phase 3 | Feature 17: Skill Normalization
Leverages local Ollama LLM to resolve ambiguous terms and suggest canonical matches.
Strictly constrained by structured JSON outputs and false-merge validation.
"""

import json
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings
from app.services.ollama_client import post_ollama_chat
from app.services.skills.false_merge_guard import validate_canonical_assignment

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a strict, precise Skill Normalization Assistant for a technical career platform.
Your task is to analyze candidate skill mentions that are ambiguous or unknown and suggest whether they map to an established canonical technology name.

CRITICAL RULES:
1. NEVER merge distinct technologies:
   - Java and JavaScript must NEVER be merged.
   - React and React Native must NEVER be merged.
   - Python and PyTorch must NEVER be merged.
   - AWS and Azure must NEVER be merged.
   - SQL and PostgreSQL must NEVER be merged.
   - Git and GitHub must NEVER be merged.
   - LangChain and LangGraph must NEVER be merged.
   - Machine Learning and Deep Learning must NEVER be merged.
2. If an ambiguous term (like 'R' or 'Go') is used without technical evidence, do NOT force a mapping.
3. If an input is unknown, preserve it as the canonical name with is_known=false.
4. Output ONLY a valid JSON object matching this schema:
{
  "suggestions": [
    {
      "original_name": string,
      "canonical_name": string,
      "category": "Programming Languages" | "Frameworks & Libraries" | "Databases" | "Cloud & DevOps" | "Machine Learning & AI" | "Tools" | "Soft Skills" | "Other",
      "skill_type": "technical" | "soft" | "tool",
      "is_known": boolean,
      "confidence": float (between 0.0 and 1.0)
    }
  ]
}
"""


class SkillAIExtractor:
    """Ollama AI service for skill disambiguation."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def suggest_canonical_mappings(
        self,
        unresolved_skills: List[str],
        context_text: Optional[str] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Queries Ollama to suggest canonical mappings for unresolved or ambiguous skill names.
        Returns parsed list of suggestions or None if Ollama is unreachable/fails.
        """
        if not unresolved_skills:
            return []

        payload_items = unresolved_skills[:20]  # Limit batch size
        context_snippet = (context_text[:1500] if context_text else "No extra context provided.")

        user_content = (
            f"Analyze these ambiguous or unknown skill mentions in the context of the resume:\n\n"
            f"Skills: {json.dumps(payload_items)}\n\n"
            f"Context: {context_snippet}\n"
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
                logger.info(
                    "Ollama skill suggestion returned non-200 status %s", response.status_code
                )
                return None

            data = response.json()
            message_content = data.get("message", {}).get("content", "")
            if not message_content:
                return None

            parsed = json.loads(message_content)
            raw_suggestions = parsed.get("suggestions", [])
            if not isinstance(raw_suggestions, list):
                return None

            # Validate each suggestion against false merge guardrails
            validated = []
            for item in raw_suggestions:
                orig = item.get("original_name")
                canon = item.get("canonical_name")
                if orig and canon:
                    if validate_canonical_assignment(orig, canon):
                        validated.append(item)
                    else:
                        logger.warning(
                            "AI suggested false merge rejected by guardrail: %s -> %s", orig, canon
                        )
                        # Fallback to preserving original
                        validated.append({
                            "original_name": orig,
                            "canonical_name": orig,
                            "category": "Other",
                            "skill_type": "technical",
                            "is_known": False,
                            "confidence": 0.3,
                        })

            return validated

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.info("Ollama unavailable for skill suggestion (%s). Graceful fallback.", exc)
            return None
        except Exception as exc:
            logger.warning("Error during AI skill suggestion: %s", exc)
            return None


skill_ai_extractor = SkillAIExtractor()
