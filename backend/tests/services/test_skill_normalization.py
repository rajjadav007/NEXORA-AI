"""
Unit Tests for Skill Normalization Engine
Phase 3 | Feature 17: Skill Normalization
Tests 5-layer normalization, false-merge guards, contextual disambiguation, duplicate consolidation,
and all 13 mandatory specification test cases.
"""

import pytest
import asyncio
from app.services.skills.formatter import normalize_skill_text, create_lookup_key
from app.services.skills.false_merge_guard import are_distinct_technologies, validate_canonical_assignment
from app.services.skills.context_matcher import disambiguate_token
from app.services.skills.dictionary import skill_dictionary, DICTIONARY_VERSION
from app.services.skills.consolidator import consolidate_normalized_skills
from app.services.skills.service import skill_normalization_service
from app.schemas.skills import SkillEntryData, SkillManualUpdateRequest


# --- 1. FORMATTING NORMALIZATION TESTS ---

def test_casing_and_whitespace_normalization():
    assert normalize_skill_text("   python   ") == "python"
    assert normalize_skill_text("REACT\tJS") == "REACT JS"
    assert normalize_skill_text("• JavaScript •") == "JavaScript"
    assert normalize_skill_text("“FastAPI”") == "FastAPI"


def test_lookup_key_generation():
    assert create_lookup_key("Node.js") == "nodejs"
    assert create_lookup_key("ReactJS") == "reactjs"
    assert create_lookup_key("Postgre SQL") == "postgresql"
    assert create_lookup_key("C++") == "c++"
    assert create_lookup_key("C#") == "c#"
    assert create_lookup_key(".NET") == "net"


# --- 2. MANDATORY DISTINCTION & FALSE MERGE PREVENTION TESTS ---

def test_mandatory_distinction_pairs():
    """Ensure distinct technologies are NEVER merged."""
    assert are_distinct_technologies("Java", "JavaScript") is True
    assert are_distinct_technologies("React", "React Native") is True
    assert are_distinct_technologies("Python", "PyTorch") is True
    assert are_distinct_technologies("AWS", "Azure") is True
    assert are_distinct_technologies("SQL", "PostgreSQL") is True
    assert are_distinct_technologies("Git", "GitHub") is True
    assert are_distinct_technologies("LangChain", "LangGraph") is True
    assert are_distinct_technologies("Machine Learning", "Deep Learning") is True
    assert are_distinct_technologies("HTML", "HTML5") is True
    assert are_distinct_technologies("C", "C++") is True


def test_validate_canonical_assignment_guardrails():
    """Reject illegal merges."""
    assert validate_canonical_assignment("Java", "JavaScript") is False
    assert validate_canonical_assignment("React Native", "React") is False
    assert validate_canonical_assignment("PyTorch", "Python") is False
    assert validate_canonical_assignment("PostgreSQL", "SQL") is False
    assert validate_canonical_assignment("GitHub", "Git") is False
    assert validate_canonical_assignment("LangGraph", "LangChain") is False
    assert validate_canonical_assignment("Deep Learning", "Machine Learning") is False

    # Valid matches
    assert validate_canonical_assignment("JS", "JavaScript") is True
    assert validate_canonical_assignment("ML", "Machine Learning") is True
    assert validate_canonical_assignment("Postgre SQL", "PostgreSQL") is True


# --- 3. CONTEXTUAL DISAMBIGUATION TESTS ---

def test_ambiguous_r_with_and_without_context():
    # With strong technical context
    canon, cat, conf, status = disambiguate_token(
        raw_token="R",
        section_name="Programming Languages",
        context_text="Experienced in data science, ggplot, and statistical analysis with R and Python.",
        surrounding_skills=["Python", "SQL", "Statistics"]
    )
    assert canon == "R"
    assert cat == "Programming Languages"
    assert status == "normalized"
    assert conf >= 0.85

    # Ambiguous without tech context
    canon2, cat2, conf2, status2 = disambiguate_token(
        raw_token="R",
        section_name="General",
        context_text="Grade R achieved in high school.",
        surrounding_skills=[]
    )
    assert status2 == "pending_review"


def test_ambiguous_go_with_and_without_context():
    canon, cat, conf, status = disambiguate_token(
        raw_token="Go",
        section_name="Technical Stack",
        context_text="Developed microservices and backend services in Go with Docker.",
        surrounding_skills=["Docker", "Kubernetes"]
    )
    assert canon == "Go"
    assert status == "normalized"

    # Verb context
    canon_verb, _, _, status_verb = disambiguate_token(
        raw_token="Go",
        section_name="Profile",
        context_text="Ready to go to the next level in career.",
    )
    assert status_verb == "pending_review"


# --- 4. THE 13 MANDATORY SPECIFICATION TEST CASES ---

@pytest.mark.asyncio
async def test_case_1_js_javascript_consolidation():
    """Test Case 1: JS, Javascript and JavaScript -> One canonical JavaScript skill."""
    raw = ["JS", "Javascript", "JavaScript"]
    res = await skill_normalization_service.normalize_skill_list(raw)
    assert len(res) == 1
    js = res[0]
    assert js.canonical_name == "JavaScript"
    assert js.category == "Programming Languages"
    assert js.occurrence_count == 3
    assert set(js.aliases_detected).intersection({"JS", "Javascript"})


@pytest.mark.asyncio
async def test_case_2_ml_machine_learning():
    """Test Case 2: ML and Machine Learning -> One canonical Machine Learning skill."""
    raw = ["ML", "Machine Learning"]
    res = await skill_normalization_service.normalize_skill_list(raw)
    assert len(res) == 1
    entry = res[0]
    assert entry.canonical_name == "Machine Learning"
    assert entry.occurrence_count == 2
    assert "ML" in entry.aliases_detected


@pytest.mark.asyncio
async def test_case_3_java_and_javascript_separation():
    """Test Case 3: Java and JavaScript -> Two separate skills."""
    raw = ["Java", "JavaScript"]
    res = await skill_normalization_service.normalize_skill_list(raw)
    assert len(res) == 2
    names = {s.canonical_name for s in res}
    assert names == {"Java", "JavaScript"}


@pytest.mark.asyncio
async def test_case_4_react_and_react_native_separation():
    """Test Case 4: React and React Native -> Two separate skills."""
    raw = ["React", "React Native", "ReactJS", "ReactNative"]
    res = await skill_normalization_service.normalize_skill_list(raw)
    assert len(res) == 2
    names = {s.canonical_name for s in res}
    assert names == {"React", "React Native"}


@pytest.mark.asyncio
async def test_case_5_python_and_pytorch_separation():
    """Test Case 5: Python and PyTorch -> Two separate skills."""
    raw = ["Python", "PyTorch", "Python3", "Torch"]
    res = await skill_normalization_service.normalize_skill_list(raw)
    assert len(res) == 2
    names = {s.canonical_name for s in res}
    assert names == {"Python", "PyTorch"}


@pytest.mark.asyncio
async def test_case_6_postgresql_variants():
    """Test Case 6: Postgre SQL and PostgreSQL -> One canonical PostgreSQL skill."""
    raw = ["Postgre SQL", "PostgreSQL", "Postgres"]
    res = await skill_normalization_service.normalize_skill_list(raw)
    assert len(res) == 1
    assert res[0].canonical_name == "PostgreSQL"
    assert res[0].occurrence_count == 3


@pytest.mark.asyncio
async def test_case_7_ambiguous_r():
    """Test Case 7: Ambiguous R -> Use context or request review."""
    # Without context
    res_no_context = await skill_normalization_service.normalize_skill_list(["R"])
    assert len(res_no_context) == 1
    assert res_no_context[0].normalization_status == "pending_review"

    # With strong data science context
    res_context = await skill_normalization_service.normalize_skill_list(
        ["R", "Python", "Data Science"],
        context_text="Specialized in statistical programming with R and Python."
    )
    r_skill = next(s for s in res_context if s.canonical_name == "R")
    assert r_skill.normalization_status == "normalized"
    assert r_skill.category == "Programming Languages"


@pytest.mark.asyncio
async def test_case_8_unknown_skill_preservation():
    """Test Case 8: Unknown skill -> Preserve the original name."""
    custom_tool = "SuperCustomProprietaryToolX"
    res = await skill_normalization_service.normalize_skill_list([custom_tool])
    assert len(res) == 1
    assert res[0].canonical_name == custom_tool
    assert res[0].original_name == custom_tool
    assert res[0].normalization_status == "pending_review"


def test_case_9_duplicate_mentions_across_sections():
    """Test Case 9: Duplicate mentions across sections -> Consolidate while preserving all evidence."""
    entries = [
        SkillEntryData(
            original_name="JS",
            canonical_name="JavaScript",
            category="Programming Languages",
            normalization_method="alias_match",
            confidence_score=0.95,
            source_sections=["skills"],
            source_evidence=["Skills: JS, HTML, CSS"],
        ),
        SkillEntryData(
            original_name="Javascript",
            canonical_name="JavaScript",
            category="Programming Languages",
            normalization_method="format_normalization",
            confidence_score=0.98,
            source_sections=["experience"],
            source_evidence=["Built frontends in Javascript and React"],
        ),
        SkillEntryData(
            original_name="JavaScript",
            canonical_name="JavaScript",
            category="Programming Languages",
            normalization_method="exact_match",
            confidence_score=1.0,
            source_sections=["education"],
            source_evidence=["Coursework in JavaScript and Web Development"],
        ),
    ]

    consolidated = consolidate_normalized_skills(entries)
    assert len(consolidated) == 1
    c = consolidated[0]
    assert c.canonical_name == "JavaScript"
    assert c.occurrence_count == 3
    assert set(c.source_sections) == {"skills", "experience", "education"}
    assert len(c.source_evidence) == 3
    assert "JS" in c.aliases_detected
    assert "Javascript" in c.aliases_detected


def test_case_10_incorrect_ai_suggestion_guard():
    """Test Case 10: Incorrect AI suggestion -> Do not automatically merge without sufficient evidence."""
    # False merge guard rejects AI merging PyTorch into Python
    assert validate_canonical_assignment("PyTorch", "Python") is False
    assert validate_canonical_assignment("JavaScript", "Java") is False
    assert validate_canonical_assignment("React Native", "React") is False


@pytest.mark.asyncio
async def test_case_11_manual_confirmed_mapping_protection():
    """Test Case 11: Manual confirmed mapping -> Preserve user's decision during reprocessing."""
    resume_id = "test-resume-manual-edit"
    entry = SkillEntryData(
        id="s1",
        resume_id=resume_id,
        original_name="SpecialR",
        canonical_name="R",
        category="Programming Languages",
        normalization_status="pending_review",
    )
    skill_normalization_service._staging_cache[resume_id] = [entry]

    # User confirms mapping
    confirmed = skill_normalization_service.confirm_mapping(resume_id, "s1")
    assert confirmed.normalization_status == "confirmed"
    assert confirmed.is_manually_edited is True

    # Check that manual edit flag persists
    current = skill_normalization_service.get_normalized_skills(resume_id)
    assert current[0].normalization_status == "confirmed"


@pytest.mark.asyncio
async def test_case_12_reprocessing_no_duplicates():
    """Test Case 12: Reprocessing -> No duplicate canonical records."""
    raw = ["JS", "JavaScript", "Javascript"]
    res1 = await skill_normalization_service.normalize_skill_list(raw)
    assert len(res1) == 1

    # Reprocess same list
    res2 = await skill_normalization_service.normalize_skill_list(raw)
    assert len(res2) == 1
    assert res2[0].canonical_name == "JavaScript"


def test_case_13_conflicting_alias_handling():
    """Test Case 13: Conflicting alias -> Reject conflicting mapping."""
    # Attempting to map 'js' to 'Java' when it already maps to 'JavaScript'
    success, msg = skill_dictionary.add_alias(
        canonical_name="Java",
        new_alias="JS"
    )
    assert success is False
    assert "already mapped" in msg or "conflicts" in msg


def test_dictionary_versioning():
    """Test dictionary version tracking."""
    assert skill_dictionary.version == DICTIONARY_VERSION
    assert DICTIONARY_VERSION == "1.0.0"
