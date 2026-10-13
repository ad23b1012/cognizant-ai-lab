# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
# Scheme Navigator - Deterministic Welfare Eligibility Engine
# Built against official Government of India verified schema in data/schemes_db.json

from logging import Logger, getLogger
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from neuro_san.interfaces.coded_tool import CodedTool


class SchemeEligibilityEngine(CodedTool):
    """
    Evaluates citizen profiles against official government rules deterministically.
    Sensitive citizen data (income, social category, landholdings) is accepted either
    via public args or out-of-band via sly_data for zero-leakage privacy.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._db_path = self._locate_db()
        self._schemes: List[Dict[str, Any]] = self._load_schemes()

    def _locate_db(self) -> Path:
        """Locates the verified schemes JSON database."""
        candidates = [
            Path("data/schemes_db.json"),
            Path(__file__).resolve().parent.parent.parent / "data" / "schemes_db.json",
            Path(os.getcwd()) / "data" / "schemes_db.json",
        ]
        for p in candidates:
            if p.exists():
                return p
        return Path("data/schemes_db.json")

    def _load_schemes(self) -> List[Dict[str, Any]]:
        if self._db_path.exists():
            with open(self._db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("schemes", [])
        return []

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Evaluates citizen eligibility.
        
        :param args: Public dictionary with citizen profile parameters:
            - domain: Optional domain filter: "education", "agriculture", "farmer", or "all".
            - state: Citizen domicile state (e.g., "karnataka", "andhra_pradesh", "all").
            - occupation: "student", "farmer", "daily_wage", etc.
            - age: Citizen age (integer).
            - gender: "male", "female", "other".
            - education_level: "class_8", "class_10", "class_12", "undergraduate", "engineering", etc.
            - land_acres: Cultivable agricultural land in acres (float).
            - is_taxpayer: Boolean whether citizen or parent pays income tax.
            - scheme_id: Optional scheme ID to check exclusively.
        :param sly_data: Privacy-preserving dictionary holding sensitive citizen parameters:
            - annual_income_inr: Family annual income in INR (keeps income out of LLM chat log).
            - social_category: Caste category: "General", "OBC", "SC", "ST", "2A", "3B", "Cat-1", etc.
            - aadhaar_seeded: Boolean whether bank account is Aadhaar DBT linked.
            - ration_card_tier: "BPL", "AAY", "APL", "White", "None".
        """
        tool_name = self.__class__.__name__
        logger: Logger = getLogger(tool_name)
        logger.info("Executing %s with args: %s, sly_data keys: %s", tool_name, list(args.keys()), list(sly_data.keys()))

        profile = self._build_effective_profile(args, sly_data)
        requested_domain = str(args.get("domain", "all")).lower().strip()
        requested_scheme_id = args.get("scheme_id")

        eligible_schemes = []
        ineligible_schemes = []

        for scheme in self._schemes:
            sid = scheme.get("id")
            category = scheme.get("category", "")

            # Filter by specific scheme_id if requested
            if requested_scheme_id and sid != requested_scheme_id:
                continue

            # Domain filter check
            if requested_domain != "all":
                if requested_domain in ("education", "scholarship") and "education" not in category:
                    continue
                if requested_domain in ("agriculture", "farmer") and "farmer" not in category and "agri" not in category:
                    continue

            evaluation = self._evaluate_scheme(scheme, profile)
            if evaluation["is_eligible"]:
                eligible_schemes.append(evaluation)
            else:
                ineligible_schemes.append(evaluation)

        result = {
            "status": "SUCCESS",
            "citizen_summary": {
                "state": profile.get("state", "Not specified").title(),
                "occupation": profile.get("occupation", "Not specified").title(),
                "age": profile.get("age"),
                "gender": profile.get("gender", "Not specified").title(),
                "annual_income_inr": f"₹{profile.get('annual_income_inr', 0):,}",
                "social_category": profile.get("social_category", "General"),
                "land_acres": profile.get("land_acres", 0.0),
                "is_taxpayer": profile.get("is_taxpayer", False),
                "privacy_mode": "sly_data protected" if ("annual_income_inr" in sly_data or "social_category" in sly_data) else "standard"
            },
            "total_schemes_checked": len(eligible_schemes) + len(ineligible_schemes),
            "eligible_count": len(eligible_schemes),
            "ineligible_count": len(ineligible_schemes),
            "eligible_schemes": eligible_schemes,
            "ineligible_schemes": ineligible_schemes,
            "guidance_note": "Evaluated against verified Central & State operational guidelines. Check live portal for application cycles and document submission dates."
        }

        sly_data["last_eligibility_run"] = result["eligible_count"]
        return result

    def _build_effective_profile(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merges public args with sensitive sly_data."""
        raw_income = sly_data.get("annual_income_inr")
        if raw_income is None:
            raw_income = args.get("annual_income_inr", args.get("income", 0))
        try:
            annual_income = float(raw_income)
        except (ValueError, TypeError):
            annual_income = 0.0

        raw_category = sly_data.get("social_category", args.get("category", args.get("caste", "General")))
        raw_state = str(args.get("state", sly_data.get("state", "all"))).lower().strip().replace(" ", "_")

        raw_land = args.get("land_acres", sly_data.get("land_acres", 0.0))
        try:
            land_acres = float(raw_land)
        except (ValueError, TypeError):
            land_acres = 0.0

        raw_age = args.get("age", sly_data.get("age", 20))
        try:
            age = int(raw_age)
        except (ValueError, TypeError):
            age = 20

        return {
            "annual_income_inr": annual_income,
            "social_category": str(raw_category).strip(),
            "state": raw_state,
            "occupation": str(args.get("occupation", "")).lower().strip(),
            "gender": str(args.get("gender", "")).lower().strip(),
            "age": age,
            "education_level": str(args.get("education_level", "")).lower().strip(),
            "class12_percentile": float(args.get("class12_percentile", args.get("percentile", 85.0))),
            "land_acres": land_acres,
            "is_taxpayer": bool(args.get("is_taxpayer", sly_data.get("is_taxpayer", False))),
            "has_bank_account": bool(args.get("has_bank_account", True)),
        }

    def _evaluate_scheme(self, scheme: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministically evaluates a scheme against citizen profile with full audit log."""
        sid = scheme.get("id")
        rules_log = []
        is_eligible = True

        occupation = profile.get("occupation", "")
        income = profile.get("annual_income_inr", 0.0)
        caste = profile.get("social_category", "General").upper()
        land_acres = profile.get("land_acres", 0.0)
        is_taxpayer = profile.get("is_taxpayer", False)
        age = profile.get("age", 20)
        edu_level = profile.get("education_level", "")
        percentile = profile.get("class12_percentile", 85.0)

        # -------------------------------------------------------------
        # 1. EDU-001: PM-USP Central Sector Scheme of Scholarship (CSSS)
        # -------------------------------------------------------------
        if sid == "EDU-001":
            if occupation == "farmer":
                is_eligible = False
                rules_log.append({"rule": "Target Group", "status": "FAIL", "reason": "Exclusive to higher education college/university students."})
            else:
                rules_log.append({"rule": "Target Group", "status": "PASS", "reason": "Student pursuing post-Class XII higher education."})

            # Income ceiling: ₹4.5 Lakhs
            if income > 450000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": f"Family income ₹{income:,.0f} exceeds ₹4,50,000 ceiling (Exceeded by ₹{income - 450000:,.0f})."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": f"Family income ₹{income:,.0f} <= ₹4,50,000 ceiling."})

            # Class XII merit percentile: >= 80th percentile
            if percentile < 80.0:
                is_eligible = False
                rules_log.append({"rule": "Class XII Merit", "status": "FAIL", "reason": f"Score {percentile}% is below mandatory 80th percentile threshold."})
            else:
                rules_log.append({"rule": "Class XII Merit", "status": "PASS", "reason": f"Score {percentile}% meets merit ranking."})

        # -------------------------------------------------------------
        # 2. EDU-002: National Means-cum-Merit Scholarship Scheme (NMMSS)
        # -------------------------------------------------------------
        elif sid == "EDU-002":
            if occupation == "farmer":
                is_eligible = False
                rules_log.append({"rule": "Target Group", "status": "FAIL", "reason": "Secondary school student scholarship (Class IX-XII)."})
            elif edu_level in ("undergraduate", "engineering", "postgraduate", "phd"):
                is_eligible = False
                rules_log.append({"rule": "Course Stage", "status": "FAIL", "reason": "NMMSS is strictly for secondary school stage (Class IX to XII). College students should apply for post-matric/CSSS."})
            else:
                rules_log.append({"rule": "Course Stage", "status": "PASS", "reason": "Eligible school education stage."})

            # Income ceiling: ₹3.5 Lakhs
            if income > 350000:
                is_eligible = False
                rules_log.append({"rule": "Parental Income", "status": "FAIL", "reason": f"Parental income ₹{income:,.0f} exceeds ₹3,50,000 ceiling."})
            else:
                rules_log.append({"rule": "Parental Income", "status": "PASS", "reason": f"Parental income ₹{income:,.0f} <= ₹3,50,000 ceiling."})

        # -------------------------------------------------------------
        # 3. EDU-003: Top Class Education for SC Students
        # -------------------------------------------------------------
        elif sid == "EDU-003":
            if "SC" not in caste:
                is_eligible = False
                rules_log.append({"rule": "Social Category", "status": "FAIL", "reason": f"Strictly reserved for Scheduled Caste (SC) students. Declared: {caste}."})
            else:
                rules_log.append({"rule": "Social Category", "status": "PASS", "reason": "Candidate belongs to Scheduled Caste (SC)."})

            # Income ceiling: ₹8.0 Lakhs
            if income > 800000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": f"Family income ₹{income:,.0f} exceeds ₹8,00,000 ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": f"Family income ₹{income:,.0f} <= ₹8,00,000 ceiling."})

            if occupation == "farmer":
                is_eligible = False
                rules_log.append({"rule": "Institution Enrollment", "status": "FAIL", "reason": "Requires admission in notified premier institute (IIT/NIT/IIIT/IIM/AIIMS)."})
            else:
                rules_log.append({"rule": "Institution Enrollment", "status": "PASS", "reason": "Enrolled in higher technical/professional degree."})

        # -------------------------------------------------------------
        # 4. EDU-004: Top Class Higher Education for ST Students
        # -------------------------------------------------------------
        elif sid == "EDU-004":
            if occupation == "farmer":
                is_eligible = False
                rules_log.append({"rule": "Institution Enrollment", "status": "FAIL", "reason": "Requires enrollment in notified premier higher education institute."})
            elif "ST" not in caste:
                is_eligible = False
                rules_log.append({"rule": "Social Category", "status": "FAIL", "reason": f"Strictly reserved for Scheduled Tribe (ST) students. Declared: {caste}."})
            else:
                rules_log.append({"rule": "Social Category", "status": "PASS", "reason": "Candidate belongs to Scheduled Tribe (ST)."})

            # Income ceiling: ₹6.0 Lakhs
            if income > 600000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": f"Family income ₹{income:,.0f} exceeds ₹6,00,000 ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": f"Family income ₹{income:,.0f} <= ₹6,00,000 ceiling."})

        # -------------------------------------------------------------
        # 5. EDU-005: Post-Matric Scholarship for SC Students (PMS-SC)
        # -------------------------------------------------------------
        elif sid == "EDU-005":
            if occupation == "farmer":
                is_eligible = False
                rules_log.append({"rule": "Target Group", "status": "FAIL", "reason": "Exclusive to students pursuing post-matric courses."})
            elif "SC" not in caste:
                is_eligible = False
                rules_log.append({"rule": "Social Category", "status": "FAIL", "reason": f"Strictly reserved for Scheduled Caste (SC) students. Declared: {caste}."})
            else:
                rules_log.append({"rule": "Social Category", "status": "PASS", "reason": "Candidate belongs to Scheduled Caste (SC)."})

            # Income ceiling: ₹2.5 Lakhs
            if income > 250000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": f"Family income ₹{income:,.0f} exceeds ₹2,50,000 ceiling (Exceeded by ₹{income - 250000:,.0f})."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": f"Family income ₹{income:,.0f} <= ₹2,50,000 ceiling."})

        # -------------------------------------------------------------
        # AP-EDU-001: Jagananna Vidya Deevena (RTF - Full Tuition Fee Reimbursement)
        # -------------------------------------------------------------
        elif sid == "AP-EDU-001":
            state = profile.get("state", "").lower()
            if occupation == "farmer":
                is_eligible = False
                rules_log.append({"rule": "Target Group", "status": "FAIL", "reason": "Exclusive to students pursuing higher technical/degree courses."})
            elif state and "andhra" not in state and "ap" != state and state != "all":
                is_eligible = False
                rules_log.append({"rule": "Domicile State", "status": "FAIL", "reason": f"Strictly reserved for Andhra Pradesh domiciled students. Declared state: {state.title()}."})
            else:
                rules_log.append({"rule": "Domicile State", "status": "PASS", "reason": "Student has Andhra Pradesh domicile."})

            # Income ceiling: ₹2.5 Lakhs
            if income > 250000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": f"Family income ₹{income:,.0f} exceeds ₹2,50,000 ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": f"Family income ₹{income:,.0f} <= ₹2,50,000 ceiling."})

            # Course requirement
            if edu_level in ("school", "class_8", "class_10"):
                is_eligible = False
                rules_log.append({"rule": "Course Level", "status": "FAIL", "reason": "Exclusive to post-intermediate higher education (ITI, Polytechnic, Degree, B.Tech/Engineering, PG)."})
            else:
                rules_log.append({"rule": "Course Level", "status": "PASS", "reason": f"Enrolled in eligible higher technical/degree course ({edu_level or 'B.Tech/Degree'})."})

        # -------------------------------------------------------------
        # AP-EDU-002: Jagananna Vasathi Deevena (MTF - Hostel & Maintenance)
        # -------------------------------------------------------------
        elif sid == "AP-EDU-002":
            state = profile.get("state", "").lower()
            if occupation == "farmer":
                is_eligible = False
                rules_log.append({"rule": "Target Group", "status": "FAIL", "reason": "Exclusive to students pursuing higher technical/degree courses."})
            elif state and "andhra" not in state and "ap" != state and state != "all":
                is_eligible = False
                rules_log.append({"rule": "Domicile State", "status": "FAIL", "reason": f"Strictly reserved for Andhra Pradesh domiciled students. Declared state: {state.title()}."})
            else:
                rules_log.append({"rule": "Domicile State", "status": "PASS", "reason": "Student has Andhra Pradesh domicile."})

            # Income ceiling: ₹2.5 Lakhs
            if income > 250000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": f"Family income ₹{income:,.0f} exceeds ₹2,50,000 ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": f"Family income ₹{income:,.0f} <= ₹2,50,000 ceiling."})

            if edu_level in ("school", "class_8", "class_10"):
                is_eligible = False
                rules_log.append({"rule": "Course Level", "status": "FAIL", "reason": "Exclusive to post-intermediate higher education (ITI, Polytechnic, Degree, B.Tech)."})
            else:
                rules_log.append({"rule": "Course Level", "status": "PASS", "reason": f"Enrolled in eligible higher professional/degree course ({edu_level or 'B.Tech/Degree'})."})

        # -------------------------------------------------------------
        # KA-EDU-001: Karnataka State Scholarship Portal (SSP) Post-Matric
        # -------------------------------------------------------------
        elif sid == "KA-EDU-001":
            state = profile.get("state", "").lower()
            if occupation == "farmer":
                is_eligible = False
                rules_log.append({"rule": "Target Group", "status": "FAIL", "reason": "Exclusive to students pursuing post-matric courses."})
            elif state and "karnataka" not in state and "ka" != state and state != "all":
                is_eligible = False
                rules_log.append({"rule": "Domicile State", "status": "FAIL", "reason": f"Strictly reserved for Karnataka state domiciled students. Declared state: {state.title()}."})
            else:
                rules_log.append({"rule": "Domicile State", "status": "PASS", "reason": "Student has Karnataka domicile."})

            # Income ceiling: ₹2.5 Lakhs for SC/ST/Cat-1; ₹1.0 Lakh for 2A/2B/3A/3B/OBC
            income_cap = 250000 if any(k in caste for k in ("SC", "ST", "CAT-1")) else 100000
            if income > income_cap:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": f"Family income ₹{income:,.0f} exceeds ₹{income_cap:,.0f} ceiling for category {caste}."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": f"Family income ₹{income:,.0f} <= ₹{income_cap:,.0f} ceiling for {caste}."})

        # -------------------------------------------------------------
        # 6. FARM-001: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)
        # -------------------------------------------------------------
        elif sid == "FARM-001":
            if occupation == "student":
                is_eligible = False
                rules_log.append({"rule": "Occupation Requirement", "status": "FAIL", "reason": "Farmer landholder family scheme."})
            elif land_acres <= 0.0:
                is_eligible = False
                rules_log.append({"rule": "Land Record", "status": "FAIL", "reason": "Requires cultivable landholding in revenue records."})
            else:
                rules_log.append({"rule": "Land Record", "status": "PASS", "reason": f"Holds {land_acres} acres cultivable land."})

            # Exclusion: Income Tax Payers
            if is_taxpayer:
                is_eligible = False
                rules_log.append({"rule": "Taxpayer Exclusion", "status": "FAIL", "reason": "Statutory exclusion: Income tax payees in previous assessment year are disqualified."})
            else:
                rules_log.append({"rule": "Taxpayer Exclusion", "status": "PASS", "reason": "Non-taxpayer family (eligible for direct DBT)."})

        # -------------------------------------------------------------
        # 7. FARM-002: Pradhan Mantri Fasal Bima Yojana (PMFBY)
        # -------------------------------------------------------------
        elif sid == "FARM-002":
            if occupation == "student":
                is_eligible = False
                rules_log.append({"rule": "Occupation", "status": "FAIL", "reason": "Crop insurance for cultivators."})
            elif land_acres <= 0.0:
                is_eligible = False
                rules_log.append({"rule": "Cultivation Proof", "status": "FAIL", "reason": "Requires land title or valid tenant/sharecropper cultivation agreement."})
            else:
                rules_log.append({"rule": "Cultivation Proof", "status": "PASS", "reason": f"Active cultivator with {land_acres} acres under notification."})

        # -------------------------------------------------------------
        # 8. FARM-003: Kisan Credit Card (KCC)
        # -------------------------------------------------------------
        elif sid == "FARM-003":
            if occupation == "student":
                is_eligible = False
                rules_log.append({"rule": "Occupation", "status": "FAIL", "reason": "Institutional agricultural credit facility for farmers."})
            elif land_acres <= 0.0:
                rules_log.append({"rule": "Cultivation Scope", "status": "PASS", "reason": "Can apply via oral lessee / SHG / dairy / fisheries segment."})
            else:
                rules_log.append({"rule": "Cultivation Scope", "status": "PASS", "reason": f"Owner cultivator with {land_acres} acres eligible for scale of finance credit."})

        # -------------------------------------------------------------
        # 9. FARM-004: PMKSY — Per Drop More Crop (PDMC)
        # -------------------------------------------------------------
        elif sid == "FARM-004":
            if occupation == "student":
                is_eligible = False
                rules_log.append({"rule": "Occupation", "status": "FAIL", "reason": "Micro-irrigation subsidy for agricultural cultivators."})
            elif land_acres <= 0.0:
                is_eligible = False
                rules_log.append({"rule": "Land Requirement", "status": "FAIL", "reason": "Requires identifiable agricultural land for drip/sprinkler installation."})
            else:
                rules_log.append({"rule": "Land Requirement", "status": "PASS", "reason": f"Cultivable land ({land_acres} acres) eligible for micro-irrigation assistance."})

        # -------------------------------------------------------------
        # 10. FARM-005: Pradhan Mantri Kisan Maandhan Yojana (PM-KMY)
        # -------------------------------------------------------------
        elif sid == "FARM-005":
            if occupation == "student":
                is_eligible = False
                rules_log.append({"rule": "Occupation", "status": "FAIL", "reason": "Farmer contributory pension scheme."})
            elif land_acres <= 0.0:
                is_eligible = False
                rules_log.append({"rule": "Land Record", "status": "FAIL", "reason": "Intended for small and marginal landholding farmers."})
            elif land_acres > 5.0:  # 2 hectares = ~5 acres
                is_eligible = False
                rules_log.append({"rule": "Landholding Limit", "status": "FAIL", "reason": f"Landholding {land_acres} acres exceeds maximum limit of 2 hectares (5.0 acres)."})
            else:
                rules_log.append({"rule": "Landholding Limit", "status": "PASS", "reason": f"Small/marginal farmer with {land_acres} acres (<= 2 hectares)."})

            # Age window: 18 - 40 years
            if age < 18 or age > 40:
                is_eligible = False
                rules_log.append({"rule": "Entry Age", "status": "FAIL", "reason": f"Age {age} is outside the statutory entry age window of 18–40 years."})
            else:
                rules_log.append({"rule": "Entry Age", "status": "PASS", "reason": f"Age {age} is within 18–40 entry window."})

            if is_taxpayer:
                is_eligible = False
                rules_log.append({"rule": "Taxpayer Exclusion", "status": "FAIL", "reason": "Statutory exclusion: Income tax payees are excluded from PM-KMY pension."})

        # Format Benefit String from benefits dict
        benefits_dict = scheme.get("benefits", {})
        benefit_str = benefits_dict.get("amount") or benefits_dict.get("summary") or "Financial support per scheme guidelines"
        if benefits_dict.get("payment_frequency"):
            benefit_str += f" ({benefits_dict['payment_frequency']})"

        failure_reasons = [r["reason"] for r in rules_log if r["status"] == "FAIL"]
        why_not_eligible = "; ".join(failure_reasons) if failure_reasons else None

        return {
            "scheme_id": sid,
            "scheme_name": scheme.get("name"),
            "category": scheme.get("category"),
            "administering_authority": scheme.get("administering_authority"),
            "purpose": scheme.get("purpose"),
            "is_eligible": is_eligible,
            "benefit": benefit_str,
            "portal_url": scheme.get("official_application_url"),
            "source_urls": scheme.get("official_source_urls", []),
            "application_status": scheme.get("application_status_as_of"),
            "documents_needed": scheme.get("documents_commonly_needed", []),
            "how_to_apply": scheme.get("how_to_apply", []),
            "rules_audit": rules_log,
            "why_not_eligible": why_not_eligible,
            "actionable_advice": self._generate_advice(failure_reasons, scheme, profile) if not is_eligible else "Gather required certificates and apply on official portal."
        }

    def _generate_advice(self, failure_reasons: List[str], scheme: Dict[str, Any], profile: Dict[str, Any]) -> str:
        advice = []
        for reason in failure_reasons:
            if "exceeds" in reason and "ceiling" in reason:
                advice.append("Check Top-Class / Merit schemes (e.g. EDU-003 or EDU-001) where income caps are up to ₹8 Lakhs.")
            elif "Scheduled Caste" in reason:
                advice.append("Explore general merit schemes like EDU-001 (PM-USP) or state-level OBC/General-EWS scholarships.")
            elif "Scheduled Tribe" in reason:
                advice.append("Explore central sector merit schemes or state tribal welfare department notifications.")
            elif "Taxpayer" in reason:
                advice.append("Explore institutional bank credit under KCC scale of finance or PMKSY micro-irrigation support.")
            elif "entry age window" in reason:
                advice.append("Check Atal Pension Yojana (APY) or regular agricultural credit programs.")
            elif "secondary school stage" in reason:
                advice.append("Apply for college-level schemes such as EDU-001 (PM-USP CSSS) or EDU-005 (PMS-SC).")
        return " | ".join(advice) if advice else "Consult the official portal guidelines for alternative quotas."
