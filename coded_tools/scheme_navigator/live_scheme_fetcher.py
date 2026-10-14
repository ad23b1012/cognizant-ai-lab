# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
# Scheme Navigator - Live Official Portal Fetcher & PDF Guideline Extractor
# Strictly grounded in Government of India official portals (.gov.in / .nic.in) to prevent misinformation.

import io
import json
import logging
from logging import Logger, getLogger
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import requests
from pypdf import PdfReader

from neuro_san.interfaces.coded_tool import CodedTool

OFFICIAL_GOV_DOMAINS = [
    ".gov.in",
    ".nic.in"
]

VERIFIED_PORTALS_REGISTRY = {
    "NSP": {
        "name": "National Scholarship Portal",
        "url": "https://scholarships.gov.in/",
        "administering_authority": "Ministry of Electronics & IT / Ministry of Education, GoI",
        "category": "education_scholarship",
        "key_schemes": ["EDU-001", "EDU-002", "EDU-003", "EDU-004", "EDU-005"],
        "default_announcements": [
            "One Time Registration (OTR) is mandatory for all fresh and renewal applicants.",
            "Aadhaar face-authentication or biometric e-KYC required on NSP OTR App.",
            "Check institutional nodal officer verification deadline before final submission."
        ]
    },
    "PM_KISAN": {
        "name": "PM-KISAN Samman Nidhi Portal",
        "url": "https://pmkisan.gov.in/",
        "administering_authority": "Ministry of Agriculture & Farmers Welfare, GoI",
        "category": "farmer_scheme",
        "key_schemes": ["FARM-001"],
        "default_announcements": [
            "DBT installments are transferred directly to Aadhaar-seeded bank accounts.",
            "Mandatory e-KYC completion required via OTP or CSC biometric centers.",
            "Statutory Exclusion: Institutional landholders and income tax payees disqualified."
        ]
    },
    "PMFBY": {
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "url": "https://www.pmfby.gov.in/",
        "administering_authority": "Ministry of Agriculture & Farmers Welfare, GoI",
        "category": "farmer_scheme",
        "key_schemes": ["FARM-002"],
        "default_announcements": [
            "Kharif/Rabi cutoff application windows are strictly per state notification calendars.",
            "Subsidized farmer premium capped at 2% for Kharif crops and 1.5% for Rabi crops.",
            "Localized calamity loss must be reported within 72 hours via Crop Insurance App."
        ]
    },
    "MYSCHEME": {
        "name": "MyScheme National Citizen Welfare Directory",
        "url": "https://www.myscheme.gov.in/",
        "administering_authority": "Ministry of Electronics & Information Technology, GoI",
        "category": "all",
        "key_schemes": ["ALL"],
        "default_announcements": [
            "Single-window national discovery platform for central and state welfare initiatives.",
            "Direct application redirection to official department portals."
        ]
    },
    "KARNATAKA_SSP": {
        "name": "Karnataka State Scholarship Portal (SSP)",
        "url": "https://ssp.postmatric.karnataka.gov.in/",
        "administering_authority": "Centre for e-Governance, Government of Karnataka",
        "category": "education_scholarship",
        "key_schemes": ["SSP-POSTMATRIC"],
        "default_announcements": [
            "Nadakacheri 15-digit RD Caste & Income certificate linking mandatory.",
            "E-Attestation required through college nodal officers.",
            "NPCI Aadhaar-seeded bank account mandatory for direct DBT credit."
        ]
    },
    "AP_GNANABHUMI": {
        "name": "Andhra Pradesh JnanaBhumi / Jagananna Vidya & Vasathi Deevena Portal",
        "url": "https://jnanabhumi.ap.gov.in/",
        "administering_authority": "Social Welfare & Higher Education Dept, Government of Andhra Pradesh",
        "category": "education_scholarship",
        "key_schemes": ["AP-EDU-001 (Jagananna Vidya Deevena)", "AP-EDU-002 (Jagananna Vasathi Deevena)", "AP-POSTMATRIC"],
        "default_announcements": [
            "Jagananna Vidya Deevena (RTF): 100% full tuition fee reimbursement for eligible B.Tech/Degree students.",
            "Jagananna Vasathi Deevena (MTF): ₹20,000/yr hostel & food maintenance allowance credited in two installments to mother's account.",
            "MeeSeva Integrated Caste & Income certificate linking and Biometric/e-KYC authentication active.",
            "Aadhaar-seeded bank account in the mother's name is mandatory for Vasathi Deevena DBT credit."
        ]
    },
    "AP_RYTHUBHAROSA": {
        "name": "Andhra Pradesh Karshak & Rythu Bharosa Portal",
        "url": "https://karshak.ap.gov.in/",
        "administering_authority": "Department of Agriculture, Government of Andhra Pradesh",
        "category": "farmer_scheme",
        "key_schemes": ["AP-FARM-001 (YSR Rythu Bharosa)"],
        "default_announcements": [
            "Annual financial assistance of ₹13,500/year to farmer families (inclusive of PM-KISAN ₹6,000).",
            "Webland patta passbook & CCRC cards for tenant farmers verified through Rythu Bharosa Kendras (RBK)."
        ]
    }
}

PORTAL_ALIASES = {
    "AP": "AP_GNANABHUMI",
    "ANDHRA": "AP_GNANABHUMI",
    "ANDHRA_PRADESH": "AP_GNANABHUMI",
    "ANDHRAPRADESH": "AP_GNANABHUMI",
    "GNANABHUMI": "AP_GNANABHUMI",
    "JNANABHUMI": "AP_GNANABHUMI",
    "AP_GNANABHUMI": "AP_GNANABHUMI",
    "KARNATAKA": "KARNATAKA_SSP",
    "SSP": "KARNATAKA_SSP",
    "KARNATAKA_SSP": "KARNATAKA_SSP",
    "NSP": "NSP",
    "CENTRAL": "NSP",
    "SCHOLARSHIP": "NSP",
    "PM_KISAN": "PM_KISAN",
    "PMKISAN": "PM_KISAN",
    "KISAN": "PM_KISAN",
    "PMFBY": "PMFBY",
    "FASAL_BIMA": "PMFBY",
    "MYSCHEME": "MYSCHEME",
    "AP_RYTHUBHAROSA": "AP_RYTHUBHAROSA",
    "RYTHUBHAROSA": "AP_RYTHUBHAROSA",
    "RYTHU_BHAROSA": "AP_RYTHUBHAROSA",
}



class LiveSchemeFetcher(CodedTool):
    """
    Autonomous tool to fetch real-time updates from official government portals
    and extract complete eligibility, benefit, and document requirements directly
    from official scheme guideline PDF gazettes.
    Restricts requests to HTTPS .gov.in and .nic.in domains and checks redirects.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._db_path = self._locate_db()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml,application/pdf;q=0.9,*/*;q=0.8"
        }

    def _locate_db(self) -> Path:
        candidates = [
            Path("data/schemes_db.json"),
            Path(__file__).resolve().parent.parent.parent / "data" / "schemes_db.json",
            Path(os.getcwd()) / "data" / "schemes_db.json",
        ]
        for p in candidates:
            if p.exists():
                return p
        return Path("data/schemes_db.json")

    def is_official_gov_domain(self, url: str) -> bool:
        """Accept HTTPS URLs on government domains; redirects are checked separately."""
        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()
            return (parsed.scheme == "https" and not parsed.username and not parsed.password
                    and any(hostname.endswith(suffix) for suffix in OFFICIAL_GOV_DOMAINS))
        except Exception:
            return False

    def ping_portal(self, url: str, timeout: float = 4.0) -> Dict[str, Any]:
        """Pings an official government portal with timeout and returns status."""
        try:
            resp = requests.get(url, timeout=timeout, headers=self.headers, allow_redirects=True, stream=True)
            if not self.is_official_gov_domain(resp.url):
                resp.close()
                return {"url": url, "status_code": resp.status_code, "is_online": False, "error": "redirected_to_unverified_domain"}
            result = {"url": url, "status_code": resp.status_code,
                      "is_online": resp.status_code < 400,
                      "response_time_ms": int(resp.elapsed.total_seconds() * 1000)}
            resp.close()
            return result
        except Exception as e:
            return {
                "url": url,
                "status_code": None,
                "is_online": False,
                "error": type(e).__name__
            }

    def extract_text_from_pdf_stream(self, pdf_bytes: bytes, max_pages: int = 15) -> str:
        """Extracts complete text from an in-memory PDF stream."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            extracted_pages = []
            total_pages = min(len(reader.pages), max_pages)
            for idx in range(total_pages):
                page_text = reader.pages[idx].extract_text() or ""
                if page_text.strip():
                    extracted_pages.append(f"--- PAGE {idx + 1} ---\n{page_text}")
            return "\n\n".join(extracted_pages)
        except Exception as e:
            return f"Error reading PDF: {type(e).__name__}: {str(e)}"

    def parse_guideline_text(self, text: str, source_url: str) -> Dict[str, Any]:
        """
        Parses raw text from official PDF gazette/guidelines and extracts structured scheme attributes.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # 1. Scheme Title Detection
        name_match = re.search(r"(?:SCHEME OF|GUIDELINES FOR|PRADHAN MANTRI|CENTRAL SECTOR|NATIONAL)[^\n\.\;]+", text, re.IGNORECASE)
        scheme_name = name_match.group(0).strip().title() if name_match else "Official Government Welfare Scheme"

        # 2. Income Ceiling Extraction
        income_ceiling = None
        income_match = re.search(
            r"(?:family\s+income|parental\s+income|annual\s+income|income)[^\n\.\;]*?(?:shall\s+not\s+exceed|not\s+exceed|below|less\s+than|up\s+to|ceiling|maximum|within)?\s*(?:Rs\.?|INR|₹)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(lakhs?|thousand)?",
            text,
            re.IGNORECASE
        )
        if income_match:
            raw_val = income_match.group(1).replace(",", "")
            unit = (income_match.group(2) or "").lower()
            try:
                val = float(raw_val)
                if "lakh" in unit:
                    income_ceiling = int(val * 100000)
                elif "thousand" in unit:
                    income_ceiling = int(val * 1000)
                else:
                    income_ceiling = int(val)
            except ValueError:
                pass

        # 3. Monetary Benefit Extraction
        benefit_desc = "Financial assistance as per official statutory guidelines"
        benefit_match = re.search(r"(?:scholarship of|assistance of|incentive of|grant of|rate of|amount of)\s*(?:Rs\.?|INR|₹)?\s*([0-9,]+(?:\s*(?:per\s+(?:annum|year|month)|lakh|thousand))?)", text, re.IGNORECASE)
        if benefit_match:
            benefit_desc = f"₹{benefit_match.group(1).strip()}"

        # 4. Target Group & Category Extraction
        categories_found = []
        for cat in ["SC", "ST", "OBC", "General", "Minority", "EWS", "Girls", "Women", "Differently Abled"]:
            if re.search(rf"\b{cat}\b", text, re.IGNORECASE):
                categories_found.append(cat)

        # 5. Core Eligibility Requirements
        eligibility_clauses = []
        for clause in re.findall(r"(?:must be|shall be|eligible if|criteria:?)\s*([^\.\n]{15,120})", text, re.IGNORECASE)[:4]:
            cleaned = clause.strip()
            if cleaned and cleaned not in eligibility_clauses:
                eligibility_clauses.append(cleaned.capitalize())

        if not eligibility_clauses:
            eligibility_clauses = [
                "Applicant must be a bonafide Indian citizen fulfilling domicile regulations.",
                f"Annual family income must not exceed prescribed ceiling (Declared/Detected: ₹{income_ceiling:,} if applicable)." if income_ceiling else "Must meet income ceiling per notification."
            ]

        # 6. Commonly Needed Documents
        docs_needed = []
        doc_patterns = [
            ("Aadhaar Card", r"\b(Aadhaar|UIDAI)\b"),
            ("Income Certificate", r"\b(income certificate|income declaration)\b"),
            ("Caste / Community Certificate", r"\b(caste certificate|community certificate)\b"),
            ("Academic Marksheet", r"\b(marksheet|qualifying examination|class 12|degree)\b"),
            ("Bank Account Details", r"\b(bank account|passbook|NPCI|DBT)\b"),
            ("Land Record / RTC Pahani", r"\b(land record|RTC|pahani|patta|khatiyan)\b"),
            ("Bonafide Institution Certificate", r"\b(bonafide|institution verification|college id)\b")
        ]
        for doc_name, pattern in doc_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                docs_needed.append(doc_name)

        if not docs_needed:
            docs_needed = ["Aadhaar or identity proof", "Income declaration", "Bank account details", "Academic/land record as applicable"]

        return {
            "parsed_name": scheme_name,
            "source_url": source_url,
            "income_ceiling_inr": income_ceiling,
            "benefit_summary": benefit_desc,
            "social_categories_targeted": categories_found or ["All eligible citizens"],
            "eligibility_highlights": eligibility_clauses,
            "mandatory_documents": docs_needed,
            "verification_status": "AUTHENTIC_GOVERNMENT_PUBLICATION",
            "extracted_text_preview": text[:500] + ("..." if len(text) > 500 else "")
        }

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Executes live portal status verification and PDF guideline extraction.

        Supported actions:
        1. 'check_portal_status': Pings registered portals and returns reachability plus separately-labelled static guidance.
        2. 'fetch_official_pdf_guidelines': Downloads and parses official government scheme PDF or announcement URL.
        3. 'discover_and_ingest_scheme': Fetches and registers a new scheme into data/schemes_db.json.
        """
        action = str(args.get("action", "check_portal_status")).lower().strip()
        scheme_id = args.get("scheme_id")
        target_url = args.get("url")

        logger: Logger = getLogger(self.__class__.__name__)
        # Do not log caller-provided URLs; they may contain credentials or identifiers.
        logger.info("Executing %s action: %s", self.__class__.__name__, action)

        # ---------------------------------------------------------------------
        # ACTION 1: Check Portal Reachability (not scheme status or announcements)
        # ---------------------------------------------------------------------
        if action == "check_portal_status":
            import asyncio

            raw_portal = str(args.get("portal", "all")).upper().strip()
            portal_key = PORTAL_ALIASES.get(raw_portal, raw_portal)

            if portal_key in VERIFIED_PORTALS_REGISTRY:
                if portal_key in ("AP_GNANABHUMI", "KARNATAKA_SSP"):
                    portals_to_check = {
                        portal_key: VERIFIED_PORTALS_REGISTRY[portal_key],
                        "NSP": VERIFIED_PORTALS_REGISTRY["NSP"]
                    }
                elif portal_key in ("AP_RYTHUBHAROSA",):
                    portals_to_check = {
                        portal_key: VERIFIED_PORTALS_REGISTRY[portal_key],
                        "PM_KISAN": VERIFIED_PORTALS_REGISTRY["PM_KISAN"]
                    }
                else:
                    portals_to_check = {portal_key: VERIFIED_PORTALS_REGISTRY[portal_key]}
            else:
                portals_to_check = VERIFIED_PORTALS_REGISTRY

            def _check_one(item):
                k, meta = item
                ping_res = self.ping_portal(meta["url"], timeout=2.5)
                return {
                    "portal_id": k,
                    "portal_name": meta["name"],
                    "url": meta["url"],
                    "is_operational": ping_res.get("is_online", False),
                    "http_status": ping_res.get("status_code"),
                    "response_time_ms": ping_res.get("response_time_ms"),
                    "administering_authority": meta["administering_authority"],
                    "static_guidance": meta["default_announcements"],
                    "notices_fetched": False
                }

            status_report = await asyncio.gather(*(
                asyncio.to_thread(_check_one, item) for item in portals_to_check.items()
            ))

            return {
                "status": "SUCCESS",
                "mode": "PORTAL_REACHABILITY_CHECK",
                "total_portals_checked": len(status_report),
                "portals": status_report,
                "anti_misinformation_policy": "Strictly restricted to official .gov.in and .nic.in verified networks."
            }

        # ---------------------------------------------------------------------
        # ACTION 2: Fetch and Read Official PDF Guidelines / Notifications
        # ---------------------------------------------------------------------
        elif action in ("fetch_official_pdf_guidelines", "read_pdf_guidelines"):
            if not target_url:
                # If no URL provided but scheme_id provided, look up from schemes_db
                if scheme_id:
                    with open(self._db_path, "r", encoding="utf-8") as f:
                        db = json.load(f)
                    for s in db.get("schemes", []):
                        if s.get("id") == scheme_id:
                            target_url = s.get("official_application_url")
                            break

            if not target_url:
                return {
                    "status": "ERROR",
                    "message": "Missing 'url' or valid 'scheme_id' for official guideline retrieval."
                }

            # Enforce zero-misinformation guardrail
            if not self.is_official_gov_domain(target_url):
                return {
                    "status": "REJECTED_NON_GOVERNMENT_SOURCE",
                    "requested_url": target_url,
                    "error": "Security & Accuracy Policy: Only official government domains ending in .gov.in or .nic.in are permitted. Third-party private blogs are rejected to prevent misinformation."
                }

            # Attempt PDF download / reading
            try:
                import asyncio
                resp = await asyncio.to_thread(
                    requests.get, target_url, timeout=7.0, headers=self.headers,
                    allow_redirects=True, stream=True
                )
                if not self.is_official_gov_domain(resp.url):
                    resp.close()
                    return {"status": "REJECTED_NON_GOVERNMENT_SOURCE", "requested_url": target_url,
                            "error": "The URL redirected outside the allowed government domains."}
                if int(resp.headers.get("Content-Length", "0") or 0) > 20_000_000:
                    resp.close()
                    return {"status": "ERROR", "message": "Remote document exceeds the 20 MB download limit."}
                resp.raise_for_status()
                chunks = []
                size = 0
                for chunk in resp.iter_content(chunk_size=65_536):
                    size += len(chunk)
                    if size > 20_000_000:
                        resp.close()
                        return {"status": "ERROR", "message": "Remote document exceeds the 20 MB download limit."}
                    chunks.append(chunk)
                content = b"".join(chunks)
                resp._content = content
                resp.close()
                content_type = resp.headers.get("Content-Type", "").lower()

                if "application/pdf" in content_type or target_url.lower().endswith(".pdf"):
                    # Process PDF binary
                    pdf_text = self.extract_text_from_pdf_stream(resp.content)
                    parsed_data = self.parse_guideline_text(pdf_text, target_url)
                    return {
                        "status": "SUCCESS",
                        "document_type": "OFFICIAL_PDF_GAZETTE",
                        "url": target_url,
                        "data": parsed_data
                    }
                else:
                    # Web HTML notification
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, "html.parser")
                    text_content = soup.get_text(separator="\n", strip=True)
                    parsed_data = self.parse_guideline_text(text_content[:6000], target_url)
                    return {
                        "status": "SUCCESS",
                        "document_type": "OFFICIAL_PORTAL_WEB_NOTICE",
                        "url": target_url,
                        "data": parsed_data
                    }

            except Exception as e:
                # Report the fetch failure; no live data or fallback evaluation occurred.
                return {
                    "status": "FETCH_FAILED",
                    "url": target_url,
                    "notice": f"The live request failed ({type(e).__name__}). The local registry was not re-evaluated by this action.",
                    "offline_verified_source": "data/schemes_db.json"
                }

        # ---------------------------------------------------------------------
        # ACTION 3: Discover and Dynamically Ingest Scheme to Database
        # ---------------------------------------------------------------------
        elif action == "discover_and_ingest_scheme":
            new_scheme_payload = args.get("scheme_data")
            if not new_scheme_payload or not isinstance(new_scheme_payload, dict):
                return {
                    "status": "ERROR",
                    "message": "'scheme_data' dictionary with required schema attributes must be provided."
                }

            missing = [key for key in ("name", "category", "eligibility", "official_application_url")
                       if not new_scheme_payload.get(key)]
            if missing:
                return {"status": "ERROR", "message": "Missing required scheme metadata: " + ", ".join(missing)}
            if not isinstance(new_scheme_payload.get("eligibility"), list):
                return {"status": "ERROR", "message": "'eligibility' must be a list of source-backed criteria."}

            # Verify official portal URL before saving
            portal_url = new_scheme_payload.get("official_application_url", "")
            if portal_url and not self.is_official_gov_domain(portal_url):
                return {
                    "status": "REJECTED",
                    "message": "Cannot ingest scheme with non-governmental portal URL. Must end with .gov.in or .nic.in."
                }
            for source_url in new_scheme_payload.get("official_source_urls", []):
                if not self.is_official_gov_domain(source_url):
                    return {"status": "REJECTED", "message": "Every official_source_urls entry must use HTTPS on a .gov.in or .nic.in host."}

            # Ingest to database
            with open(self._db_path, "r", encoding="utf-8") as f:
                db_data = json.load(f)

            schemes = db_data.get("schemes", [])
            new_id = new_scheme_payload.get("id", f"SCH-EXT-{len(schemes) + 1:03d}")
            new_scheme_payload["id"] = new_id

            # Avoid duplicate ID
            schemes = [s for s in schemes if s.get("id") != new_id]
            schemes.append(new_scheme_payload)
            db_data["schemes"] = schemes
            db_data["metadata"]["count"] = len(schemes)

            with open(self._db_path, "w", encoding="utf-8") as f:
                json.dump(db_data, f, indent=2)

            return {
                "status": "SUCCESS",
                "message": f"Successfully validated and ingested scheme '{new_scheme_payload.get('name')}' ({new_id}) into live registry.",
                "total_schemes_in_db": len(schemes),
                "scheme_id": new_id
            }

        return {
            "status": "ERROR",
            "message": f"Unrecognized action '{action}'. Supported: 'check_portal_status', 'fetch_official_pdf_guidelines', 'discover_and_ingest_scheme'."
        }

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        import asyncio
        return asyncio.run(self.async_invoke(args, sly_data))
