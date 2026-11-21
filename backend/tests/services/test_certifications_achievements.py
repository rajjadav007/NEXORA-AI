"""
Unit Tests for Certifications & Achievements Extraction and Analysis
Phase 3 | Feature 19: Certifications & Achievements Intelligence
"""

import pytest
import uuid
from app.services.certifications.section_detector import (
    extract_certification_and_achievement_sections,
    split_section_into_blocks,
)
from app.services.certifications.deterministic_extractor import (
    extract_deterministic_certification,
    extract_deterministic_achievement,
    detect_achievement_type_and_rank,
    detect_completion_status,
)
from app.services.certifications.skill_linker import extract_skills_from_text
from app.services.certifications.confidence_scorer import (
    compute_certification_confidence,
    compute_achievement_confidence,
)
from app.services.certifications.deduplicator import (
    deduplicate_certifications,
    deduplicate_achievements,
)


def test_section_detector_certifications_and_achievements():
    sample_text = """
JOHN DOE
Software Engineer

CERTIFICATIONS
* AWS Certified Solutions Architect - Associate | Amazon Web Services (Issued: Oct 2023)
* Certified Kubernetes Administrator (CKA) - The Linux Foundation

HONORS & AWARDS
* 1st Place Winner - HackMIT 2023 for AgriConnect project
* Finalist - Google Hash Code 2022
"""
    sections = extract_certification_and_achievement_sections(sample_text)
    assert len(sections["certifications"]) == 1
    assert "AWS" in sections["certifications"][0]["text"]
    assert len(sections["achievements"]) == 1
    assert "HackMIT" in sections["achievements"][0]["text"]


def test_deterministic_certification_extraction_full():
    block = """
AWS Certified Solutions Architect - Associate | Amazon Web Services
Credential ID: AWS-84920491
https://www.credly.com/badges/aws-architect-assoc
Issued: Oct 2023
Expires: Oct 2026
"""
    cert = extract_deterministic_certification(block)
    assert cert["certification_name"] == "AWS Certified Solutions Architect - Associate"
    assert cert["issuing_organization"] == "Amazon Web Services (AWS)"
    assert cert["credential_id"] == "AWS-84920491"
    assert "credly.com" in cert["credential_url"]
    assert cert["issue_date"] == "Oct 2023"
    assert cert["expiry_date"] == "Oct 2026"
    assert cert["completion_status"] == "completed"
    assert cert["certification_category"] == "cloud"


def test_in_progress_certification():
    block = """
Google Cloud Professional Data Engineer (Currently Pursuing)
Expected: Dec 2024
"""
    cert = extract_deterministic_certification(block)
    assert cert["completion_status"] == "in_progress"
    assert cert["certification_category"] == "cloud"


def test_hackathon_winner_vs_participant():
    # Winner
    winner_block = "1st Place Winner - Smart India Hackathon 2023, team of 6"
    win_type, win_rank = detect_achievement_type_and_rank(winner_block)
    assert win_type == "award"
    assert win_rank == "1st Place"

    # 2nd Place
    second_block = "2nd Place / 1st Runner Up at PennApps 2022"
    sec_type, sec_rank = detect_achievement_type_and_rank(second_block)
    assert sec_type == "award"
    assert sec_rank == "2nd Place"

    # Finalist
    finalist_block = "Top 10 Finalist out of 500 teams at ETHDenver 2023"
    fin_type, fin_rank = detect_achievement_type_and_rank(finalist_block)
    assert fin_type == "ranking"
    assert "Top 10" in fin_rank or "Finalist" in fin_rank

    # Participant - MUST NOT be treated as winner
    part_block = "Participant in HackPrinceton 2022"
    part_type, part_rank = detect_achievement_type_and_rank(part_block)
    assert part_type == "participation"
    assert part_rank == "Participant"


def test_research_publication():
    block = """
Neural Network Compression for Edge Devices - Published in IEEE Access, 2023
DOI: 10.1109/ACCESS.2023.1234567
Co-authored research paper on pruning techniques.
"""
    achieve = extract_deterministic_achievement(block)
    assert achieve["achievement_type"] == "publication"
    assert achieve["achievement_category"] == "publication"
    assert "10.1109/ACCESS" in achieve["achievement_url"]
    assert achieve["achievement_date"] == "2023"


def test_academic_and_scholarship():
    block = "Dean's List of Academic Excellence (2021 - 2023), Top 5% in Department"
    achieve = extract_deterministic_achievement(block)
    assert achieve["achievement_category"] == "academic"
    assert achieve["achievement_type"] == "award"

    scholarship_block = "National Merit Scholarship Recipient - Awarded full tuition grant"
    achieve2 = extract_deterministic_achievement(scholarship_block)
    assert achieve2["achievement_category"] == "scholarship"


def test_skill_linking_integration():
    block = "Deep Learning Specialization - Coursera / DeepLearning.AI covering Python, PyTorch, and TensorFlow"
    skills = extract_skills_from_text(block)
    canonical_names = [s.canonical_name for s in skills]
    assert "Python" in canonical_names or "PyTorch" in canonical_names or "TensorFlow" in canonical_names


def test_confidence_scoring():
    full_cert = {
        "certification_name": "AWS Certified Solutions Architect",
        "issuing_organization": "Amazon Web Services",
        "credential_id": "ABC1234",
        "credential_url": "https://credly.com/abc",
        "issue_date": "2023",
        "source_evidence": ["Line 1", "Line 2"],
    }
    conf = compute_certification_confidence(full_cert)
    assert conf >= 0.85

    vague_cert = {
        "certification_name": "Python course",
        "source_evidence": ["Python course"],
    }
    conf_vague = compute_certification_confidence(vague_cert)
    assert conf_vague < 0.60


def test_deduplication():
    certs = [
        {
            "certification_name": "AWS Certified Solutions Architect",
            "issuing_organization": "Amazon Web Services (AWS)",
            "credential_id": None,
            "source_evidence": ["Line A"],
        },
        {
            "certification_name": "AWS Certified Solutions Architect",
            "issuing_organization": "Amazon Web Services (AWS)",
            "credential_id": "CRED-999",
            "source_evidence": ["Line B"],
        },
    ]
    deduped = deduplicate_certifications(certs)
    assert len(deduped) == 1
    assert deduped[0]["credential_id"] == "CRED-999"
    assert len(deduped[0]["source_evidence"]) == 2
