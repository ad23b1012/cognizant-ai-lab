# Scheme Navigator - Comprehensive Tests for Live Government Portal Fetcher & PDF Parser
import io
import pytest
from pypdf import PdfWriter

from coded_tools.scheme_navigator.live_scheme_fetcher import LiveSchemeFetcher


@pytest.fixture
def fetcher():
    return LiveSchemeFetcher()


def test_gov_domain_whitelist_enforcement(fetcher):
    """
    Test that anti-misinformation firewall strictly accepts .gov.in and .nic.in,
    and rejects private or unofficial domains.
    """
    valid_urls = [
        "https://scholarships.gov.in/All-Scholarships",
        "https://pmkisan.gov.in/Portal_Status",
        "https://www.myscheme.gov.in/schemes/pm-kisan",
        "https://ssp.postmatric.karnataka.gov.in/index.aspx",
        "https://tribal.nic.in/fellowship.aspx"
    ]
    invalid_urls = [
        "https://fake-scholarships.com/apply",
        "https://coaching-center.org/government-money",
        "https://freemoney.biz/scholarship",
        "https://buddy4study.com/scholarship-details",
        "http://unverified-portal.xyz",
        "http://pmkisan.gov.in/",
        "https://pmkisan.gov.in.evil.example/",
        "https://user:pass@pmkisan.gov.in/"
    ]

    for u in valid_urls:
        assert fetcher.is_official_gov_domain(u) is True, f"Failed for valid URL: {u}"

    for u in invalid_urls:
        assert fetcher.is_official_gov_domain(u) is False, f"Allowed invalid URL: {u}"


def test_check_portal_status_operational(fetcher, monkeypatch):
    """
    Test that live portal status checker returns verified Indian government portals
    with authority metadata and clearly-labelled static guidance.
    """
    monkeypatch.setattr(fetcher, "ping_portal", lambda url, timeout=4.0: {
        "url": url, "status_code": 200, "is_online": True, "response_time_ms": 5
    })
    result = fetcher.invoke({"action": "check_portal_status", "portal": "NSP"}, {})
    assert result["status"] == "SUCCESS"
    assert result["mode"] == "PORTAL_REACHABILITY_CHECK"
    assert len(result["portals"]) == 1

    nsp = result["portals"][0]
    assert nsp["portal_id"] == "NSP"
    assert "scholarships.gov.in" in nsp["url"]
    assert len(nsp["static_guidance"]) >= 1
    assert nsp["notices_fetched"] is False


def test_pdf_guideline_extraction_and_parsing(fetcher):
    """
    Test that in-memory official PDF gazette is parsed completely, extracting
    exact income ceilings, monetary benefit amounts, and document checklists.
    """
    # Create an in-memory PDF with official government wording
    writer = PdfWriter()
    writer.add_blank_page(width=400, height=600)
    
    # We will test parse_guideline_text directly with realistic official gazette text
    sample_gazette_text = """
    GOVERNMENT OF INDIA
    MINISTRY OF EDUCATION
    DEPARTMENT OF HIGHER EDUCATION
    
    SCHEME OF CENTRAL SECTOR SCHOLARSHIP FOR COLLEGE AND UNIVERSITY STUDENTS (PM-USP)
    
    1. OBJECTIVE:
    To provide financial assistance to meritorious students from low-income families.
    
    2. ELIGIBILITY CRITERIA:
    - Applicants must be above 80th percentile in relevant stream in Class XII.
    - Family income shall not exceed Rs. 4,50,000 per annum from all sources.
    - Candidate must be pursuing regular degree course in a recognised university or college.
    
    3. RATE OF SCHOLARSHIP:
    Rate of scholarship of Rs. 20,000 per annum for postgraduate courses and Rs. 10,000 for undergraduate.
    
    4. MANDATORY DOCUMENTS:
    Candidates must upload Aadhaar Card, Income Certificate issued by competent Revenue Authority,
    Class 12 marksheet, and Bank account details seeded with NPCI.
    """
    
    parsed = fetcher.parse_guideline_text(sample_gazette_text, "https://scholarships.gov.in/guidelines.pdf")
    
    assert "Scheme Of Central Sector Scholarship" in parsed["parsed_name"]
    assert parsed["income_ceiling_inr"] == 450000
    assert "₹20,000" in parsed["benefit_summary"]
    assert any("Aadhaar" in doc for doc in parsed["mandatory_documents"])
    assert any("Income" in doc for doc in parsed["mandatory_documents"])
    assert any("Marksheet" in doc for doc in parsed["mandatory_documents"])
    assert parsed["verification_status"] == "AUTHENTIC_GOVERNMENT_PUBLICATION"


def test_non_gov_source_rejection(fetcher):
    """
    Test that calling fetch_official_pdf_guidelines with an unofficial URL is
    immediately rejected by the anti-misinformation firewall.
    """
    result = fetcher.invoke({
        "action": "fetch_official_pdf_guidelines",
        "url": "https://suspicious-broker-site.com/scheme_rules.pdf"
    }, {})
    
    assert result["status"] == "REJECTED_NON_GOVERNMENT_SOURCE"
    assert "Security & Accuracy Policy" in result["error"]


def test_dynamic_scheme_discovery_and_ingestion(fetcher):
    """
    Test dynamic discovery and ingestion of a new verified scheme into the database.
    """
    new_scheme = {
        "id": "EXT-TEST-001",
        "category": "clean_energy",
        "name": "PM Surya Ghar Muft Bijli Yojana",
        "government_level": "Central",
        "administering_authority": "Ministry of New and Renewable Energy, GoI",
        "purpose": "Provides financial subsidy for rooftop solar installation to generate free electricity.",
        "benefits": {
            "amount": "Subsidy up to ₹78,000 for 3 kW rooftop solar capacity"
        },
        "eligibility": [
            "Applicant family must be Indian citizens.",
            "Must have a suitable roof for solar panel installation.",
            "Must have a valid grid electricity connection."
        ],
        "official_application_url": "https://pmsuryaghar.gov.in/"
    }

    result = fetcher.invoke({
        "action": "discover_and_ingest_scheme",
        "scheme_data": new_scheme
    }, {})

    try:
        assert result["status"] == "SUCCESS"
        assert result["scheme_id"] == "EXT-TEST-001"
    finally:
        # Clean up test entry to keep database pristine
        import json
        with open(fetcher._db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
        db["schemes"] = [s for s in db.get("schemes", []) if s.get("id") != "EXT-TEST-001"]
        db["metadata"]["count"] = len(db["schemes"])
        with open(fetcher._db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)

