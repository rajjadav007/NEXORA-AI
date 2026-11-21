"""
AI-Powered Resume Grammar & Clarity Evaluator using LangChain and ChatOllama
Phase 4 | Feature 25: Grammar & Clarity Analysis
Reuses existing Ollama + LangChain Gemma integration to audit writing quality,
grammar, spelling, tone, wordiness, and sentence clarity without altering original facts.
"""

import logging
import time
from typing import Dict, Any, Optional, List

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.grammar_analysis import (
    ResumeGrammarAIStructuredOutput,
    GrammarIssueAI,
    SentenceComparisonAI,
    GRAMMAR_CATEGORIES,
)
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)

SYSTEM_GRAMMAR_PROMPT = """You are a senior Executive Resume Editor and Professional Business Writing Coach.
Your task is to analyze candidate resume text for writing quality, precision, professional tone, and clarity across 8 categories:
1. Grammar Mistakes (`grammar`): Subject-verb agreement, tense consistency (past tense for past roles, present for current), misplaced modifiers.
2. Spelling Errors (`spelling`): Typos, misspelled technical or common terms, incorrect homophones.
3. Sentence Clarity (`clarity`): Ambiguous phrasing, unclear antecedent pronouns, confusing clauses.
4. Professional Tone (`tone`): Casual colloquialisms, first-person pronouns (I, me, my, we), overly modest or aggressive phrasing.
5. Sentence Structure (`structure`): Run-on sentences, awkward fragments, missing action verbs, inverted clauses.
6. Repeated Words & Phrases (`repetition`): Overusing the same action verb (e.g. "Worked on", "Helped with", "Managed") across consecutive bullets.
7. Unnecessary Wording (`wordiness`): Filler words, redundant qualifiers ("successfully managed", "in order to", "various different").
8. Readability & Complexity (`readability`): Overly dense multi-line bullet points that strain recruiter scanning.

STRICT PRINCIPLES:
- PRESERVE MEANING: Keep the candidate's exact original accomplishments, technologies, dates, and metrics intact.
- NEVER INVENT: Do NOT fabricate qualifications, new metrics, imaginary responsibilities, or unmentioned achievements.
- DO NOT OVERWRITE: Present corrections as discrete suggestions for candidate review.
- FOR EVERY ISSUE: Provide exact `original_text`, polished `suggested_text`, category, clear `explanation`, and `severity` (High, Medium, Low).
- SENTENCE COMPARISONS: Provide 3 to 6 high-impact before-and-after sentence comparisons showing how unclear phrasing transforms into crisp executive prose.
- Output MUST conform strictly to the provided JSON schema.
"""

USER_GRAMMAR_TEMPLATE = """Audit the writing quality, grammar, spelling, tone, and clarity of this resume:

=== STRUCTURED RESUME CONTENT ===
{resume_summary}

=== CLEANED RESUME TEXT (EXCERPT) ===
{cleaned_text_excerpt}

Identify all writing deficiencies across the 8 categories. Provide overall_assessment, issues list, before-and-after sentence comparisons, and readability summary.
"""


class GrammarAIEvaluator:
    """LangChain + ChatOllama integration for candidate writing quality audit."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or max(settings.OLLAMA_TIMEOUT_SECONDS, 30.0)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_GRAMMAR_PROMPT),
            ("user", USER_GRAMMAR_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.1,
            timeout=self.timeout,
        )

    def _generate_fallback_analysis(
        self,
        resume_summary: str,
        cleaned_text: Optional[str],
    ) -> ResumeGrammarAIStructuredOutput:
        """Deterministic heuristic fallback if Ollama service is unreachable."""
        text = cleaned_text or resume_summary or ""
        issues: List[GrammarIssueAI] = []
        comparisons: List[SentenceComparisonAI] = []

        # Check for first-person pronouns (I, me, my)
        import re
        first_person = re.findall(r"\b(I|me|my|we|our)\b", text, re.IGNORECASE)
        if first_person:
            issues.append(
                GrammarIssueAI(
                    original_text="Use of personal pronouns: " + ", ".join(set(first_person[:4])),
                    suggested_text="Drop personal pronouns and start bullet points directly with strong action verbs.",
                    category="tone",
                    explanation="Standard professional resume convention omits first-person pronouns (I, me, my) in favor of implicit first-person action verbs.",
                    severity="Medium",
                    section="General",
                )
            )

        # Check for weak filler words
        fillers = re.findall(r"\b(responsible for|helped with|worked on|in order to|successfully)\b", text, re.IGNORECASE)
        if fillers:
            issues.append(
                GrammarIssueAI(
                    original_text=f"Passive/filler phrasing detected: '{fillers[0]}'",
                    suggested_text="Replace passive duty phrasing with dynamic outcome verbs (e.g. 'Engineered', 'Optimized', 'Delivered').",
                    category="wordiness",
                    explanation="Phrases like 'responsible for' dilute the candidate's active impact and add unnecessary length.",
                    severity="Medium",
                    section="Work Experience",
                )
            )
            comparisons.append(
                SentenceComparisonAI(
                    original_sentence=f"Responsible for {fillers[0]} tasks across the team.",
                    improved_sentence="Spearheaded critical engineering initiatives across the team, driving system reliability.",
                    reason="Replaces passive duty statement with an authoritative action verb.",
                    section="Work Experience",
                )
            )

        # Fallback comparison if none found
        if not comparisons:
            comparisons.append(
                SentenceComparisonAI(
                    original_sentence="Worked on developing web features and fixing software bugs.",
                    improved_sentence="Engineered responsive web application features and resolved high-priority backend defects.",
                    reason="Elevates casual diction to precise engineering terminology.",
                    section="Experience",
                )
            )

        return ResumeGrammarAIStructuredOutput(
            overall_assessment="Resume demonstrates clear baseline communication with opportunities to sharpen action verbs, tighten sentence structure, and remove passive filler words.",
            issues=issues,
            sentence_comparisons=comparisons,
            readability_summary="Sentence length is generally manageable. Converting remaining passive clauses to active action verbs will increase recruiter reading efficiency.",
        )

    async def evaluate_grammar(
        self,
        resume_summary: str,
        cleaned_text: Optional[str] = None,
    ) -> ResumeGrammarAIStructuredOutput:
        """
        Invokes LangChain ChatOllama structured output to analyze resume writing quality.
        Falls back to rule-based analysis if Ollama is unavailable.
        """
        cleaned_excerpt = (cleaned_text or "")[:4000]
        formatted_prompt = self.prompt.format_messages(
            resume_summary=resume_summary,
            cleaned_text_excerpt=cleaned_excerpt,
        )

        try:
            llm = self._get_llm()
            structured_llm = llm.with_structured_output(ResumeGrammarAIStructuredOutput)

            logger.info("Invoking ChatOllama for grammar analysis with model %s at %s", self.model, self.base_url)
            start_time = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            duration = time.time() - start_time
            logger.info("ChatOllama grammar analysis completed in %.2f seconds", duration)

            if isinstance(result, ResumeGrammarAIStructuredOutput):
                return result
            elif isinstance(result, dict):
                return ResumeGrammarAIStructuredOutput.model_validate(result)
            else:
                return ResumeGrammarAIStructuredOutput.model_validate(result)

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, ConnectionRefusedError) as conn_err:
            logger.warning("Ollama unavailable for grammar analysis, using fallback: %s", conn_err)
            return self._generate_fallback_analysis(resume_summary, cleaned_text)

        except ValidationError as val_err:
            logger.warning("Grammar analysis structured validation error, using fallback: %s", val_err)
            return self._generate_fallback_analysis(resume_summary, cleaned_text)

        except Exception as exc:
            logger.warning("Unexpected error in grammar analysis, using fallback: %s", exc)
            return self._generate_fallback_analysis(resume_summary, cleaned_text)


grammar_ai_evaluator = GrammarAIEvaluator()
