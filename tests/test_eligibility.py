# Scheme Navigator - Comprehensive Unit Tests
# Verified against official Government of India dataset in data/schemes_db.json
import pytest
import asyncio
from coded_tools.scheme_navigator.scheme_eligibility_engine import SchemeEligibilityEngine
from coded_tools.scheme_navigator.document_checklist_generator import DocumentChecklistGenerator
from coded_tools.scheme_navigator.application_guide import ApplicationGuide


@pytest.fixture
def eligibility_engine():
    return SchemeEligibilityEngine()


@pytest.fixture
def doc_generator():
    return DocumentChecklistGenerator()


@pytest.fixture
def app_guide():
    return ApplicationGuide()


def test_raichur_sc_student_eligibility(eligibility_engine):
    """
    Scenario: Student in Raichur (Karnataka), SC category, family income ₹1.5 Lakh, studying B.Tech.
    Should qualify for EDU-001 (PM-USP), EDU-003 (Top Class SC), and EDU-005 (PMS-SC).
    """
    args = {
        "state": "karnataka",
        "occupation": "student",
        "category": "SC",
        "annual_income_inr": 150000,
        "education_level": "engineering",
        "age": 19,
        "class12_percentile": 88.5
    }
    sly_data = {}
    result = asyncio.run(eligibility_engine.async_invoke(args, sly_data))

    assert result["status"] == "SUCCESS"
    eligible_ids = [s["scheme_id"] for s in result["eligible_schemes"]]
    
    assert "EDU-001" in eligible_ids  # PM-USP CSSS
    assert "EDU-003" in eligible_ids  # Top Class SC
    assert "EDU-005" in eligible_ids  # Post-Matric SC (PMS-SC)
    assert "EDU-004" not in eligible_ids  # ST only


def test_st_engineering_student_eligibility(eligibility_engine):
    """
    Scenario: ST student studying B.Tech with family income ₹4.0 Lakhs.
    Should qualify for EDU-001 (PM-USP) and EDU-004 (Top Class ST).
    """
    args = {
        "occupation": "student",
        "category": "ST",
        "annual_income_inr": 400000,
        "education_level": "engineering",
        "age": 20,
        "class12_percentile": 85.0
    }
    sly_data = {}
    result = asyncio.run(eligibility_engine.async_invoke(args, sly_data))

    eligible_ids = [s["scheme_id"] for s in result["eligible_schemes"]]
    assert "EDU-001" in eligible_ids  # PM-USP
    assert "EDU-004" in eligible_ids  # Top Class ST
    assert "EDU-003" not in eligible_ids  # SC only
    assert "EDU-005" not in eligible_ids  # SC only


def test_young_small_farmer_full_eligibility(eligibility_engine):
    """
    Scenario: 28-year-old small farmer in Raichur with 3 acres land, non-taxpayer.
    Should qualify for all farmer schemes including PM-KMY pension (age 18-40, <= 5 acres).
    """
    args = {
        "state": "karnataka",
        "occupation": "farmer",
        "age": 28,
        "land_acres": 3.0,
        "annual_income_inr": 85000,
        "is_taxpayer": False
    }
    sly_data = {}
    result = asyncio.run(eligibility_engine.async_invoke(args, sly_data))

    eligible_ids = [s["scheme_id"] for s in result["eligible_schemes"]]
    assert "FARM-001" in eligible_ids  # PM-KISAN
    assert "FARM-002" in eligible_ids  # PMFBY Crop Insurance
    assert "FARM-003" in eligible_ids  # KCC
    assert "FARM-004" in eligible_ids  # PMKSY Micro-irrigation
    assert "FARM-005" in eligible_ids  # PM-KMY (Kisan Maandhan Pension)


def test_older_farmer_age_limit_audit(eligibility_engine):
    """
    Scenario: 48-year-old farmer with 2.5 acres land.
    Should qualify for PM-KISAN, PMFBY, KCC, PMKSY, but NOT PM-KMY (entry age window is 18-40).
    """
    args = {
        "state": "karnataka",
        "occupation": "farmer",
        "age": 48,
        "land_acres": 2.5,
        "is_taxpayer": False
    }
    sly_data = {}
    result = asyncio.run(eligibility_engine.async_invoke(args, sly_data))

    eligible_ids = [s["scheme_id"] for s in result["eligible_schemes"]]
    assert "FARM-001" in eligible_ids
    assert "FARM-005" not in eligible_ids

    ineligible_schemes = {s["scheme_id"]: s for s in result["ineligible_schemes"]}
    assert "FARM-005" in ineligible_schemes
    assert "statutory entry age window of 18–40" in ineligible_schemes["FARM-005"]["why_not_eligible"]


def test_taxpayer_statutory_exclusion_audit(eligibility_engine):
    """
    Scenario: Farmer who pays income tax.
    Must be rejected for PM-KISAN (FARM-001) and PM-KMY (FARM-005) with clear reason.
    """
    args = {
        "state": "karnataka",
        "occupation": "farmer",
        "land_acres": 4.0,
        "annual_income_inr": 650000,
        "is_taxpayer": True
    }
    sly_data = {}
    result = asyncio.run(eligibility_engine.async_invoke(args, sly_data))

    ineligible_schemes = {s["scheme_id"]: s for s in result["ineligible_schemes"]}
    assert "FARM-001" in ineligible_schemes
    pm_kisan_eval = ineligible_schemes["FARM-001"]
    assert "Income tax payees in previous assessment year are disqualified" in pm_kisan_eval["why_not_eligible"]


def test_sly_data_privacy_vaulting(eligibility_engine):
    """
    Scenario: Sensitive fields (income & caste) passed ONLY in sly_data.
    Evaluates correctly and records that private fields were supplied through sly_data.
    """
    public_args = {
        "state": "karnataka",
        "occupation": "student",
        "education_level": "engineering",
        "age": 19,
        "class12_percentile": 90.0
    }
    private_sly_data = {
        "annual_income_inr": 120000,
        "social_category": "SC",
        "ration_card_tier": "BPL"
    }
    result = asyncio.run(eligibility_engine.async_invoke(public_args, private_sly_data))

    assert result["citizen_summary"]["privacy_mode"] == "sly_data supplied"
    eligible_ids = [s["scheme_id"] for s in result["eligible_schemes"]]
    assert "EDU-001" in eligible_ids
    assert "EDU-003" in eligible_ids
    assert "EDU-005" in eligible_ids
    assert "annual_income_inr" not in result["citizen_summary"]
    assert "social_category" not in result["citizen_summary"]
    assert "last_eligibility_run" not in private_sly_data


def test_missing_profile_fields_are_not_assumed_eligible(eligibility_engine):
    result = asyncio.run(eligibility_engine.async_invoke({"scheme_id": "EDU-001"}, {}))
    assert result["status"] == "NEEDS_INFORMATION"
    assert result["eligible_count"] == 0
    assert {"occupation", "annual_income_inr", "class12_percentile"}.issubset(result["needs_information"][0]["missing_fields"])


def test_invalid_values_and_string_boolean(eligibility_engine):
    invalid = asyncio.run(eligibility_engine.async_invoke({"annual_income_inr": "unknown"}, {}))
    assert invalid["status"] == "INVALID_INPUT"
    result = asyncio.run(eligibility_engine.async_invoke({
        "scheme_id": "FARM-001", "occupation": "farmer", "land_acres": 1, "is_taxpayer": "false"
    }, {}))
    assert [s["scheme_id"] for s in result["eligible_schemes"]] == ["FARM-001"]


def test_unknown_or_unimplemented_scheme_not_eligible(eligibility_engine):
    unknown = asyncio.run(eligibility_engine.async_invoke({"scheme_id": "DOES-NOT-EXIST"}, {}))
    assert unknown["status"] == "NOT_FOUND"
    eligibility_engine._schemes.append({"id": "EXT-TEST", "name": "New metadata only", "category": "education"})
    result = asyncio.run(eligibility_engine.async_invoke({"scheme_id": "EXT-TEST"}, {}))
    assert result["unsupported_schemes"][0]["status"] == "RULES_NOT_IMPLEMENTED"
    assert result["eligible_count"] == 0


def test_document_checklist_generation(doc_generator):
    """
    Test that DocumentChecklistGenerator returns official documents with issuing authorities.
    """
    args = {"scheme_ids": ["EDU-001", "FARM-001"], "state": "karnataka"}
    sly_data = {}
    result = asyncio.run(doc_generator.async_invoke(args, sly_data))

    assert result["status"] == "SUCCESS"
    assert result["total_schemes_covered"] == 2
    doc_names = [d["document_name"] for d in result["consolidated_checklist"]]
    assert any("Aadhaar" in name for name in doc_names)
    assert any("Income" in name for name in doc_names)


def test_application_guide_walkthrough(app_guide):
    """
    Test that ApplicationGuide returns official URLs and steps for PM-KISAN (FARM-001).
    """
    args = {"scheme_id": "FARM-001"}
    sly_data = {}
    result = asyncio.run(app_guide.async_invoke(args, sly_data))

    assert result["status"] == "SUCCESS"
    assert result["scheme_id"] == "FARM-001"
    assert "https://pmkisan.gov.in" in result["official_application_url"]
    assert len(result["step_by_step_instructions"]) >= 3
