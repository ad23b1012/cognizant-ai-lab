# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
# Scheme Navigator - Deterministic Welfare Eligibility Engine
# Uses curated scheme metadata plus separately implemented Python rules.

from logging import Logger, getLogger
import json
import os
from pathlib import Path
import math
from typing import Any, Dict, List, Optional, Union

from neuro_san.interfaces.coded_tool import CodedTool


class SchemeEligibilityEngine(CodedTool):
    """
    Screens citizen profiles against the Python eligibility rules implemented here.
    Deterministic output does not establish that a rule is current or complete.
    Sensitive citizen data is accepted only through sly_data; deployments must
    ensure the client and runtime preserve that private channel.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._db_path = self._locate_db()
        self._registry_metadata: Dict[str, Any] = {}
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
                self._registry_metadata = data.get("metadata", {})
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
            - scheme_id: Optional scheme ID to check exclusively.
        :param sly_data: Privacy-preserving dictionary holding sensitive citizen parameters:
            - annual_income_inr: Family annual income in INR (keeps income out of LLM chat log).
            - social_category: Caste category: "General", "OBC", "SC", "ST", "2A", "3B", "Cat-1", etc.
            - aadhaar_seeded: Boolean whether bank account is Aadhaar DBT linked.
            - ration_card_tier: "BPL", "AAY", "APL", "White", "None".
        """
        tool_name = self.__class__.__name__
        logger: Logger = getLogger(tool_name)
        # Never log profile values or even sensitive field names. Tool arguments may
        # contain citizen information even when the caller did not use sly_data.
        logger.info("Executing %s", tool_name)
        private_argument_keys = {
            "annual_income_inr", "income", "social_category", "category", "caste",
            "land_acres", "is_taxpayer", "has_bank_account", "ration_card_tier", "aadhaar_seeded",
        }
        supplied_private_args = [
            key for key in private_argument_keys
            if args.get(key) is not None and args.get(key) != ""
        ]
        if supplied_private_args:
            return {
                "status": "PRIVATE_INPUT_REQUIRED",
                "message": "Sensitive profile fields must be supplied through the private sly_data channel, not tool arguments.",
                "fields_rejected": supplied_private_args,
            }

        private_sly_keys = {
            "annual_income_inr", "social_category", "land_acres", "is_taxpayer",
            "has_bank_account", "ration_card_tier", "aadhaar_seeded",
        }
        has_private_values = any(
            sly_data.get(key) is not None and sly_data.get(key) != ""
            for key in private_sly_keys
        )
        if has_private_values and sly_data.get("privacy_consent") is not True:
            return {
                "status": "CONSENT_REQUIRED",
                "message": "The citizen must explicitly consent before private profile values are used for screening.",
            }
        try:
            profile, missing_profile_fields = self._build_effective_profile(args, sly_data)
        except ValueError as exc:
            return {"status": "INVALID_INPUT", "message": str(exc)}
        requested_domain = str(args.get("domain", "all")).lower().strip()
        requested_scheme_id = args.get("scheme_id")

        domain_aliases = {"scholarship": "education", "farmer": "agriculture"}
        requested_domain = domain_aliases.get(requested_domain, requested_domain)
        if requested_domain not in {"all", "education", "agriculture"}:
            return {"status": "INVALID_INPUT", "message": f"Unsupported domain: {requested_domain}. Use all, education, or agriculture."}
        known_ids = {s.get("id") for s in self._schemes}
        if requested_scheme_id and requested_scheme_id not in known_ids:
            return {"status": "NOT_FOUND", "message": f"Unknown scheme_id: {requested_scheme_id}"}

        eligible_schemes = []
        ineligible_schemes = []
        needs_information = []
        unsupported_schemes = []

        for scheme in self._schemes:
            sid = scheme.get("id")
            category = scheme.get("category", "")

            # Filter by specific scheme_id if requested
            if requested_scheme_id and sid != requested_scheme_id:
                continue

            # Domain filter check
            if requested_domain != "all":
                if requested_domain == "education" and "education" not in category:
                    continue
                if requested_domain == "agriculture" and "farmer" not in category and "agri" not in category:
                    continue

            if sid not in self._supported_scheme_ids():
                unsupported_schemes.append({
                    "scheme_id": sid,
                    "scheme_name": scheme.get("name"),
                    "status": "RULES_NOT_IMPLEMENTED",
                    "source_urls": scheme.get("official_source_urls", []),
                    "source_reviewed_as_of": self._registry_metadata.get("as_of"),
                })
                continue
            required = self._required_fields(sid)
            missing = [name for name in required if profile.get(name) is None]
            if missing:
                needs_information.append({
                    "scheme_id": sid,
                    "scheme_name": scheme.get("name"),
                    "status": "NEEDS_INFORMATION",
                    "missing_fields": missing,
                    "source_urls": scheme.get("official_source_urls", []),
                    "source_reviewed_as_of": self._registry_metadata.get("as_of"),
                })
                continue

            evaluation = self._evaluate_scheme(scheme, profile)
            if evaluation["is_eligible"]:
                eligible_schemes.append(evaluation)
            else:
                ineligible_schemes.append(evaluation)

        result = {
            "status": "NEEDS_INFORMATION" if needs_information and not eligible_schemes and not ineligible_schemes else "SUCCESS",
            "registry_as_of": self._registry_metadata.get("as_of"),
            "registry_verification_policy": self._registry_metadata.get("verification_policy"),
            "citizen_summary": {
                "state": (profile.get("state") or "Not specified").replace("_", " ").title(),
                "occupation": (profile.get("occupation") or "Not specified").title(),
                "privacy_mode": (
                    "sly_data supplied" if any(
                        sly_data.get(key) is not None and sly_data.get(key) != ""
                        for key in private_sly_keys
                    )
                    else "no sensitive values supplied"
                )
            },
            "total_schemes_checked": len(eligible_schemes) + len(ineligible_schemes) + len(needs_information) + len(unsupported_schemes),
            "schemes_evaluated": len(eligible_schemes) + len(ineligible_schemes),
            "eligible_count": len(eligible_schemes),
            "ineligible_count": len(ineligible_schemes),
            "eligible_schemes": eligible_schemes,
            "ineligible_schemes": ineligible_schemes,
            "needs_information": needs_information,
            "unsupported_schemes": unsupported_schemes,
            "missing_profile_fields": missing_profile_fields,
            "guidance_note": "Rule-based screening only. Confirm current criteria and application dates with the official scheme authority."
        }
        return result

    @staticmethod
    def _supported_scheme_ids():
        return {"EDU-001", "EDU-002", "EDU-003", "EDU-004", "EDU-005", "AP-EDU-001", "AP-EDU-002", "KA-EDU-001", "FARM-001", "FARM-002", "FARM-003", "FARM-004", "FARM-005"}

    @staticmethod
    def _required_fields(scheme_id: str) -> List[str]:
        requirements = {
            "EDU-001": ["occupation", "annual_income_inr", "class12_percentile"],
            "EDU-002": ["occupation", "annual_income_inr", "education_level"],
            "EDU-003": ["occupation", "annual_income_inr", "social_category"],
            "EDU-004": ["occupation", "annual_income_inr", "social_category"],
            "EDU-005": ["occupation", "annual_income_inr", "social_category"],
            "AP-EDU-001": ["occupation", "annual_income_inr", "state", "education_level"],
            "AP-EDU-002": ["occupation", "annual_income_inr", "state", "education_level"],
            "KA-EDU-001": ["occupation", "annual_income_inr", "state", "social_category"],
            "FARM-001": ["occupation", "land_acres", "is_taxpayer"],
            "FARM-002": ["occupation", "land_acres"],
            "FARM-003": ["occupation", "land_acres"],
            "FARM-004": ["occupation", "land_acres"],
            "FARM-005": ["occupation", "land_acres", "age", "is_taxpayer"],
        }
        return requirements.get(scheme_id, [])

    def _build_effective_profile(self, args: Dict[str, Any], sly_data: Dict[str, Any]):
        """Merge public and private inputs; preserve missing values as unknown."""
        def number(value, name, *, integer=False):
            if value is None or value == "":
                return None
            if isinstance(value, bool):
                raise ValueError(f"{name} must be a number, not a boolean.")
            try:
                parsed_number = float(value)
            except (ValueError, TypeError, OverflowError):
                raise ValueError(f"{name} must be a valid {'integer' if integer else 'number'}.")
            if not math.isfinite(parsed_number) or parsed_number < 0:
                raise ValueError(f"{name} must be a finite non-negative value.")
            if integer and not parsed_number.is_integer():
                raise ValueError(f"{name} must be a whole number.")
            parsed = int(parsed_number) if integer else parsed_number
            if integer and parsed > 130:
                raise ValueError("age must be between 0 and 130.")
            return parsed

        def boolean(value, name):
            if value is None or value == "":
                return None
            if isinstance(value, bool):
                return value
            if isinstance(value, int) and value in (0, 1):
                return bool(value)
            if isinstance(value, str) and value.strip().lower() in {"true", "yes", "1"}:
                return True
            if isinstance(value, str) and value.strip().lower() in {"false", "no", "0"}:
                return False
            raise ValueError(f"{name} must be true or false.")

        raw_income = sly_data.get("annual_income_inr")
        if raw_income is None:
            raw_income = args.get("annual_income_inr", args.get("income"))
        raw_category = sly_data.get("social_category", args.get("category", args.get("caste")))
        raw_state = args.get("state", sly_data.get("state"))
        raw_land = args.get("land_acres", sly_data.get("land_acres"))
        raw_age = args.get("age", sly_data.get("age"))
        percentile = args.get("class12_percentile", args.get("percentile"))
        occupation = args.get("occupation")
        level = args.get("education_level")
        profile = {
            "annual_income_inr": number(raw_income, "annual_income_inr"),
            "social_category": str(raw_category).strip().upper() if raw_category not in (None, "") else None,
            "state": str(raw_state).lower().strip().replace(" ", "_") if raw_state not in (None, "") else None,
            "occupation": str(occupation).lower().strip() if occupation not in (None, "") else None,
            "gender": str(args.get("gender", "")).lower().strip(),
            "age": number(raw_age, "age", integer=True),
            "education_level": str(level).lower().strip() if level not in (None, "") else None,
            "class12_percentile": number(percentile, "class12_percentile"),
            "land_acres": number(raw_land, "land_acres"),
            "is_taxpayer": boolean(args.get("is_taxpayer", sly_data.get("is_taxpayer")), "is_taxpayer"),
            "has_bank_account": boolean(args.get("has_bank_account"), "has_bank_account"),
        }
        if profile["class12_percentile"] is not None and profile["class12_percentile"] > 100:
            raise ValueError("class12_percentile must be between 0 and 100.")
        return profile, [key for key, value in profile.items() if value is None]

    def _evaluate_scheme(self, scheme: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministically evaluates a scheme against citizen profile with full audit log."""
        sid = scheme.get("id")
        rules_log = []
        is_eligible = True

        occupation = profile.get("occupation", "")
        income = profile.get("annual_income_inr", 0.0)
        caste = (profile.get("social_category") or "").upper().strip()
        is_sc = caste in {"SC", "SCHEDULED CASTE", "SCHEDULED CASTES"}
        is_st = caste in {"ST", "SCHEDULED TRIBE", "SCHEDULED TRIBES"}
        land_acres = profile.get("land_acres", 0.0)
        is_taxpayer = profile.get("is_taxpayer", False)
        age = profile.get("age", 20)
        edu_level = profile.get("education_level", "")
        percentile = profile.get("class12_percentile", 85.0)

        # -------------------------------------------------------------
        # 1. EDU-001: PM-USP Central Sector Scheme of Scholarship (CSSS)
        # -------------------------------------------------------------
        if sid == "EDU-001":
            if occupation != "student":
                is_eligible = False
                rules_log.append({"rule": "Target Group", "status": "FAIL", "reason": "Exclusive to higher education college/university students."})
            else:
                rules_log.append({"rule": "Target Group", "status": "PASS", "reason": "Student pursuing post-Class XII higher education."})

            # Income ceiling: ₹4.5 Lakhs
            if income > 450000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": "Family income exceeds the applicable income ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": "Family income meets the applicable income ceiling."})

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
            if occupation != "student":
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
                rules_log.append({"rule": "Parental Income", "status": "FAIL", "reason": "Family income exceeds the applicable income ceiling."})
            else:
                rules_log.append({"rule": "Parental Income", "status": "PASS", "reason": "Family income meets the applicable income ceiling."})

        # -------------------------------------------------------------
        # 3. EDU-003: Top Class Education for SC Students
        # -------------------------------------------------------------
        elif sid == "EDU-003":
            if not is_sc:
                is_eligible = False
                rules_log.append({"rule": "Social Category", "status": "FAIL", "reason": "This scheme requires the Scheduled Caste (SC) category."})
            else:
                rules_log.append({"rule": "Social Category", "status": "PASS", "reason": "Candidate belongs to Scheduled Caste (SC)."})

            # Income ceiling: ₹8.0 Lakhs
            if income > 800000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": "Family income exceeds the applicable income ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": "Family income meets the applicable income ceiling."})

            if occupation != "student":
                is_eligible = False
                rules_log.append({"rule": "Institution Enrollment", "status": "FAIL", "reason": "Requires admission in notified premier institute (IIT/NIT/IIIT/IIM/AIIMS)."})
            else:
                rules_log.append({"rule": "Institution Enrollment", "status": "PASS", "reason": "Enrolled in higher technical/professional degree."})

        # -------------------------------------------------------------
        # 4. EDU-004: Top Class Higher Education for ST Students
        # -------------------------------------------------------------
        elif sid == "EDU-004":
            if occupation != "student":
                is_eligible = False
                rules_log.append({"rule": "Institution Enrollment", "status": "FAIL", "reason": "Requires enrollment in notified premier higher education institute."})
            elif not is_st:
                is_eligible = False
                rules_log.append({"rule": "Social Category", "status": "FAIL", "reason": "This scheme requires the Scheduled Tribe (ST) category."})
            else:
                rules_log.append({"rule": "Social Category", "status": "PASS", "reason": "Candidate belongs to Scheduled Tribe (ST)."})

            # Income ceiling: ₹6.0 Lakhs
            if income > 600000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": "Family income exceeds the applicable income ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": "Family income meets the applicable income ceiling."})

        # -------------------------------------------------------------
        # 5. EDU-005: Post-Matric Scholarship for SC Students (PMS-SC)
        # -------------------------------------------------------------
        elif sid == "EDU-005":
            if occupation != "student":
                is_eligible = False
                rules_log.append({"rule": "Target Group", "status": "FAIL", "reason": "Exclusive to students pursuing post-matric courses."})
            elif not is_sc:
                is_eligible = False
                rules_log.append({"rule": "Social Category", "status": "FAIL", "reason": "This scheme requires the Scheduled Caste (SC) category."})
            else:
                rules_log.append({"rule": "Social Category", "status": "PASS", "reason": "Candidate belongs to Scheduled Caste (SC)."})

            # Income ceiling: ₹2.5 Lakhs
            if income > 250000:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": "Family income exceeds the applicable income ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": "Family income meets the applicable income ceiling."})

        # -------------------------------------------------------------
        # AP-EDU-001: Jagananna Vidya Deevena (RTF - Full Tuition Fee Reimbursement)
        # -------------------------------------------------------------
        elif sid == "AP-EDU-001":
            state = profile.get("state", "").lower()
            if occupation != "student":
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
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": "Family income exceeds the applicable income ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": "Family income meets the applicable income ceiling."})

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
            if occupation != "student":
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
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": "Family income exceeds the applicable income ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": "Family income meets the applicable income ceiling."})

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
            if occupation != "student":
                is_eligible = False
                rules_log.append({"rule": "Target Group", "status": "FAIL", "reason": "Exclusive to students pursuing post-matric courses."})
            elif state and "karnataka" not in state and "ka" != state and state != "all":
                is_eligible = False
                rules_log.append({"rule": "Domicile State", "status": "FAIL", "reason": f"Strictly reserved for Karnataka state domiciled students. Declared state: {state.title()}."})
            else:
                rules_log.append({"rule": "Domicile State", "status": "PASS", "reason": "Student has Karnataka domicile."})

            # Income ceiling: ₹2.5 Lakhs for SC/ST/Cat-1; ₹1.0 Lakh for 2A/2B/3A/3B/OBC
            income_cap = 250000 if is_sc or is_st or caste in {"CAT-1", "CATEGORY-1", "CAT 1", "CATEGORY 1"} else 100000
            if income > income_cap:
                is_eligible = False
                rules_log.append({"rule": "Income Ceiling", "status": "FAIL", "reason": "Family income exceeds the applicable income ceiling."})
            else:
                rules_log.append({"rule": "Income Ceiling", "status": "PASS", "reason": "Family income meets the applicable income ceiling."})

        # -------------------------------------------------------------
        # 6. FARM-001: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)
        # -------------------------------------------------------------
        elif sid == "FARM-001":
            if occupation != "farmer":
                is_eligible = False
                rules_log.append({"rule": "Occupation Requirement", "status": "FAIL", "reason": "Farmer landholder family scheme."})
            elif land_acres <= 0.0:
                is_eligible = False
                rules_log.append({"rule": "Land Record", "status": "FAIL", "reason": "Requires cultivable landholding in revenue records."})
            else:
                rules_log.append({"rule": "Land Record", "status": "PASS", "reason": "Records indicate a cultivable landholding."})

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
            if occupation != "farmer":
                is_eligible = False
                rules_log.append({"rule": "Occupation", "status": "FAIL", "reason": "Crop insurance for cultivators."})
            elif land_acres <= 0.0:
                is_eligible = False
                rules_log.append({"rule": "Cultivation Proof", "status": "FAIL", "reason": "Requires land title or valid tenant/sharecropper cultivation agreement."})
            else:
                rules_log.append({"rule": "Cultivation Proof", "status": "PASS", "reason": "Active cultivator with land under the applicable notification."})

        # -------------------------------------------------------------
        # 8. FARM-003: Kisan Credit Card (KCC)
        # -------------------------------------------------------------
        elif sid == "FARM-003":
            if occupation != "farmer":
                is_eligible = False
                rules_log.append({"rule": "Occupation", "status": "FAIL", "reason": "Institutional agricultural credit facility for farmers."})
            elif land_acres <= 0.0:
                rules_log.append({"rule": "Cultivation Scope", "status": "PASS", "reason": "Can apply via oral lessee / SHG / dairy / fisheries segment."})
            else:
                rules_log.append({"rule": "Cultivation Scope", "status": "PASS", "reason": "Owner cultivator may be eligible for scale of finance credit."})

        # -------------------------------------------------------------
        # 9. FARM-004: PMKSY — Per Drop More Crop (PDMC)
        # -------------------------------------------------------------
        elif sid == "FARM-004":
            if occupation != "farmer":
                is_eligible = False
                rules_log.append({"rule": "Occupation", "status": "FAIL", "reason": "Micro-irrigation subsidy for agricultural cultivators."})
            elif land_acres <= 0.0:
                is_eligible = False
                rules_log.append({"rule": "Land Requirement", "status": "FAIL", "reason": "Requires identifiable agricultural land for drip/sprinkler installation."})
            else:
                rules_log.append({"rule": "Land Requirement", "status": "PASS", "reason": "Cultivable land is recorded for the micro-irrigation application."})

        # -------------------------------------------------------------
        # 10. FARM-005: Pradhan Mantri Kisan Maandhan Yojana (PM-KMY)
        # -------------------------------------------------------------
        elif sid == "FARM-005":
            if occupation != "farmer":
                is_eligible = False
                rules_log.append({"rule": "Occupation", "status": "FAIL", "reason": "Farmer contributory pension scheme."})
            elif land_acres <= 0.0:
                is_eligible = False
                rules_log.append({"rule": "Land Record", "status": "FAIL", "reason": "Intended for small and marginal landholding farmers."})
            elif land_acres > 5.0:  # 2 hectares = ~5 acres
                is_eligible = False
                rules_log.append({"rule": "Landholding Limit", "status": "FAIL", "reason": "Landholding exceeds the maximum limit of 2 hectares."})
            else:
                rules_log.append({"rule": "Landholding Limit", "status": "PASS", "reason": "The reported landholding is within the 2 hectare limit."})

            # Age window: 18 - 40 years
            if age < 18 or age > 40:
                is_eligible = False
                rules_log.append({"rule": "Entry Age", "status": "FAIL", "reason": "Age is outside the statutory entry window of 18–40 years."})
            else:
                rules_log.append({"rule": "Entry Age", "status": "PASS", "reason": "Age is within the statutory 18–40 entry window."})

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
            "source_reviewed_as_of": self._registry_metadata.get("as_of"),
            "verification_notes": scheme.get("verification_notes"),
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
