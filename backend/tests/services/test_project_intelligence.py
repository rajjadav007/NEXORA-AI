"""
Unit Tests for Project Intelligence Engine
Phase 3 | Feature 18: Project Intelligence
"""

import pytest
from app.services.projects.normalizer import (
    normalize_project_title,
    classify_project_category,
    extract_and_categorize_urls,
)
from app.services.projects.section_detector import (
    extract_project_sections,
    split_section_into_project_blocks,
)
from app.services.projects.skill_linker import link_technologies_to_canonical_skills
from app.services.projects.deterministic_extractor import (
    extract_technologies_from_block,
    extract_dates_and_ongoing,
    extract_team_information,
    extract_measurable_outcomes_and_achievements,
    extract_deterministic_project,
)
from app.services.projects.deduplicator import deduplicate_projects
from app.services.projects.confidence_scorer import compute_project_confidence
from app.schemas.projects import ProjectEntryData, ProjectSkillLinkData, ProjectLinkData


# --- 1. TITLE NORMALIZATION & CATEGORY CLASSIFICATION ---

def test_project_title_normalization():
    assert normalize_project_title("  AI Career Coach (Final Year Project)  ") == "AI Career Coach (Final Year Project)"
    assert normalize_project_title("E-Commerce Microservices | Python, React") == "E-Commerce Microservices"
    assert normalize_project_title("## Smart Health Assistant - github.com/user/app") == "Smart Health Assistant"
    assert normalize_project_title("“Real-Time Chat App”") == "Real-Time Chat App"


def test_project_category_classification():
    assert classify_project_category("Senior Thesis Machine Learning Model", "Academic Projects") == "academic"
    assert classify_project_category("Weather Tracker Side Project", "Personal Projects") == "personal"
    assert classify_project_category("DevPost Hackathon Winner - SafeRoute", "Projects") == "hackathon"
    assert classify_project_category("Genomic Variant Benchmarking published in IEEE", "Research") == "research"
    assert classify_project_category("Contributor to Apache Airflow with merged PR", "Open Source") == "open_source"
    assert classify_project_category("Payment Gateway Migration enterprise production system", "Professional Experience") == "professional"
    assert classify_project_category("Client Landing Page & CRM on Upwork", "Freelance Projects") == "freelance"
    assert classify_project_category("Simple Utility Script", "Projects") == "other"


def test_url_extraction_and_categorization():
    text = (
        "Check code at https://github.com/nexora/career-ai and live demo at "
        "https://career-ai.demo.app with docs at https://career-ai.readthedocs.io/en/docs"
    )
    links = extract_and_categorize_urls(text)
    assert len(links) >= 2

    types = {l.type: l.url for l in links}
    assert "github" in types
    assert "https://github.com/nexora/career-ai" in types["github"]
    assert "demo" in types or "website" in types


# --- 2. SECTION DETECTION & BLOCK SPLITTING ---

def test_section_detection_and_block_splitting():
    resume_text = """
Jane Doe
jane@example.com

ACADEMIC PROJECTS
Autonomous Driving Robot | Fall 2023
- Built ROS2 path planner with Python and C++.
- Reduced obstacle latency by 30%.
- GitHub: https://github.com/jane/robot

Distributed Key-Value Store | Go
- Designed Raft consensus protocol in Go.
- Supported 50,000 requests/sec across 5 nodes.

PROFESSIONAL EXPERIENCE
Acme Corp - Software Engineer
    """
    sections = extract_project_sections(resume_text)
    assert len(sections) == 1
    assert "ACADEMIC PROJECTS" in sections[0]["section_name"].upper()

    blocks = split_section_into_project_blocks(sections[0]["text"])
    assert len(blocks) == 2

    assert "Autonomous Driving Robot" in blocks[0]
    assert "Distributed Key-Value Store" in blocks[1]


# --- 3. SKILL LINKING WITH FEATURE 17 CANONICAL DICTIONARY ---

def test_skill_linking_to_canonical_dictionary():
    technologies = ["JS", "ReactJS", "FastAPI", "K8s", "Postgre SQL", "PyTorch", "UnknownCustomLib123"]
    canon_names, linked = link_technologies_to_canonical_skills(technologies)
    assert len(canon_names) >= 5

    name_to_canonical = {item.original_name: item.canonical_name for item in linked}
    assert name_to_canonical["JS"] == "JavaScript"
    assert name_to_canonical["ReactJS"] == "React"
    assert name_to_canonical["FastAPI"] == "FastAPI"
    assert name_to_canonical["K8s"] == "Kubernetes"
    assert name_to_canonical["Postgre SQL"] == "PostgreSQL"
    assert name_to_canonical["PyTorch"] == "PyTorch"


# --- 4. DETERMINISTIC EXTRACTION ---

def test_extract_technologies():
    text = "Technologies: Python, FastAPI, Docker, Redis, React"
    techs = extract_technologies_from_block(text)
    assert "Python" in techs
    assert "FastAPI" in techs
    assert "Docker" in techs
    assert "Redis" in techs
    assert "React" in techs


def test_extract_dates_and_ongoing():
    start, end, ongoing = extract_dates_and_ongoing("Jan 2023 - Present")
    assert "2023" in (start or "")
    assert ongoing is True

    start2, end2, ongoing2 = extract_dates_and_ongoing("March 2022 to December 2022")
    assert "2022" in (start2 or "")
    assert "2022" in (end2 or "")
    assert ongoing2 is False


def test_extract_team_info():
    team_type, team_size, role = extract_team_information("Collaborated in a team of 4 software engineers")
    assert team_type == "team"
    assert team_size == 4

    team_type2, team_size2, role2 = extract_team_information("Built as a solo project for independent study")
    assert team_type2 == "individual"


def test_extract_metrics_and_outcomes():
    lines = [
        "Accelerated API response time by 45%",
        "Successfully served 10,000+ daily active users",
        "Won 1st prize at university innovation contest",
    ]
    achievements, measurable = extract_measurable_outcomes_and_achievements(lines)
    assert len(measurable) >= 1
    assert any("45%" in m for m in measurable)
    assert len(achievements) >= 1
    assert any("1st prize" in a.lower() for a in achievements)


# --- 5. DEDUPLICATION & MERGING ---

def test_project_deduplication():
    proj1 = {
        "project_title": "Cloud File Storage",
        "normalized_title": "Cloud File Storage",
        "project_category": "personal",
        "technologies": ["Python", "FastAPI"],
        "source_evidence": ["Personal Project: Cloud File Storage built with Python."],
        "project_links": [],
        "responsibilities": ["Built backend"],
        "skills": [],
    }
    proj2 = {
        "project_title": "Cloud File Storage Service",
        "normalized_title": "Cloud File Storage",
        "project_category": "personal",
        "technologies": ["Docker", "AWS S3"],
        "source_evidence": ["Github: https://github.com/user/cloud-storage"],
        "project_links": [ProjectLinkData(type="github", url="https://github.com/user/cloud-storage")],
        "responsibilities": ["Configured docker"],
        "skills": [],
    }
    proj3 = {
        "project_title": "Blockchain Voting Protocol",
        "normalized_title": "Blockchain Voting Protocol",
        "project_category": "academic",
        "technologies": ["Solidity"],
        "source_evidence": ["Academic thesis on Blockchain Voting."],
        "project_links": [],
        "responsibilities": [],
        "skills": [],
    }

    merged = deduplicate_projects([proj1, proj2, proj3])
    assert len(merged) == 2

    storage_proj = next(p for p in merged if p["normalized_title"] == "Cloud File Storage")
    assert "Python" in storage_proj["technologies"]
    assert "Docker" in storage_proj["technologies"]
    assert len(storage_proj["project_links"]) == 1


# --- 6. CONFIDENCE SCORING ---

def test_confidence_scoring():
    high_proj = {
        "project_title": "Distributed Cache",
        "normalized_title": "Distributed Cache",
        "short_description": "In-memory cache cluster with consistent hashing",
        "detailed_description": "In-memory distributed cache cluster with consistent hashing ring and high throughput",
        "problem_statement": "High database load during traffic spikes",
        "proposed_solution": "Built consistent hashing distributed cache",
        "technologies": ["Go", "Redis"],
        "start_date": "2023-01",
        "responsibilities": ["Implemented consistent hashing ring"],
        "measurable_outcomes": ["Decreased p99 query latency by 60%"],
        "project_links": [ProjectLinkData(type="github", url="https://github.com/user/cache")],
        "source_evidence": ["Original text block with clear evidence"],
    }
    score_high = compute_project_confidence(high_proj)
    assert score_high >= 0.85

    low_proj = {
        "project_title": "Misc App",
        "normalized_title": "Misc App",
        "short_description": "App",
        "source_evidence": ["Misc App"],
    }
    score_low = compute_project_confidence(low_proj)
    assert score_low < 0.60
