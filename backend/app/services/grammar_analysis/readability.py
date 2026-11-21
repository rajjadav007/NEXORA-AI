"""
Readability and Text Complexity Metrics Engine
Phase 4 | Feature 25: Grammar & Clarity Analysis
"""

import re
from typing import Dict, Any

from app.schemas.grammar_analysis import ReadabilityMetrics


def count_syllables_word(word: str) -> int:
    """Estimates syllables in a single English word."""
    clean = re.sub(r"[^a-zA-Z]", "", word.lower())
    if not clean:
        return 1
    if len(clean) <= 3:
        return 1

    # Remove silent e at end
    if clean.endswith("e") and not clean.endswith("le"):
        clean = clean[:-1]

    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    for char in clean:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel

    return max(1, count)


def compute_readability_metrics(text: str) -> ReadabilityMetrics:
    """
    Computes reading ease, grade level, and average sentence length.
    Uses simplified Flesch Reading Ease algorithm adapted for resume bullet text.
    """
    raw_sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if len(s.strip()) > 3]
    num_sentences = max(1, len(raw_sentences))

    words = re.findall(r"\b[A-Za-z0-9'-]+\b", text)
    num_words = max(1, len(words))

    num_syllables = sum(count_syllables_word(w) for w in words)

    avg_words_per_sentence = round(num_words / num_sentences, 1)
    avg_syllables_per_word = num_syllables / num_words

    # Flesch Reading Ease: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
    raw_score = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
    readability_score = round(max(10.0, min(100.0, raw_score)), 1)

    if readability_score >= 70:
        grade_level = "Easy to Read (Grade 7-8)"
        complexity = "Clear, direct phrasing that is quick for recruiters to scan."
    elif readability_score >= 50:
        grade_level = "Professional (Grade 10-12)"
        complexity = "Optimal standard for technical and corporate resumes; professional and accessible."
    elif readability_score >= 30:
        grade_level = "College Level"
        complexity = "Slightly complex sentence structures; consider shortening dense bullet points."
    else:
        grade_level = "Dense / Academic"
        complexity = "High reading complexity; recommend trimming compound clauses and jargon."

    return ReadabilityMetrics(
        readability_score=readability_score,
        grade_level=grade_level,
        avg_words_per_sentence=avg_words_per_sentence,
        total_words=num_words,
        complexity_assessment=complexity,
    )
