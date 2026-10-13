# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
# Scheme Navigator - Document Checklist & Issuing Authority Generator
# Adapted for official Government of India verified schemes_db.json

from logging import Logger, getLogger
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from neuro_san.interfaces.coded_tool import CodedTool


class DocumentChecklistGenerator(CodedTool):
    """
    Produces actionable document checklists for eligible government schemes.
    Specifies exact issuing authorities, DigiLocker integration tips,
    and state e-governance procurement methods.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._db_path = self._locate_db()
        self._schemes: Dict[str, Dict[str, Any]] = self._load_schemes_map()

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

    def _load_schemes_map(self) -> Dict[str, Dict[str, Any]]:
        if self._db_path.exists():
            with open(self._db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {s["id"]: s for s in data.get("schemes", [])}
        return {}

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Generates document checklist.
        :param args: Dictionary with:
            - scheme_id: Single scheme ID (e.g., "EDU-001", "FARM-001") or
            - scheme_ids: List of scheme IDs (e.g. ["EDU-001", "EDU-005"])
            - state: Optional state for localized issuing authority advice.
        :param sly_data: Dictionary for runtime state.
        :return: Structured document preparation dossier.
        """
        tool_name = self.__class__.__name__
        logger: Logger = getLogger(tool_name)
        logger.info("Generating document checklist for: %s", args)

        requested_ids = []
        if "scheme_id" in args:
            requested_ids.append(args["scheme_id"])
        if "scheme_ids" in args and isinstance(args["scheme_ids"], list):
            requested_ids.extend(args["scheme_ids"])

        requested_ids = list(dict.fromkeys(requested_ids))
        if not requested_ids:
            requested_ids = list(self._schemes.keys())

        schemes_dossier = []
        master_documents = {}
        state = str(args.get("state", "")).lower().strip()

        for sid in requested_ids:
            scheme = self._schemes.get(sid)
            if not scheme:
                continue

            raw_docs = scheme.get("documents_commonly_needed", [])
            doc_items = []
            for d in raw_docs:
                auth = self._determine_authority(d, state)
                tip = self._get_acquisition_tip(d, state)
                doc_items.append({
                    "name": d,
                    "issuing_authority": auth,
                    "digital_tip": tip
                })

                if d not in master_documents:
                    master_documents[d] = {
                        "document_name": d,
                        "issuing_authority": auth,
                        "used_for_schemes": [scheme.get("name")],
                        "digital_acquisition_tips": tip
                    }
                else:
                    master_documents[d]["used_for_schemes"].append(scheme.get("name"))

            schemes_dossier.append({
                "scheme_id": sid,
                "scheme_name": scheme.get("name"),
                "portal_url": scheme.get("official_application_url"),
                "total_documents_needed": len(doc_items),
                "documents": doc_items
            })

        response = {
            "status": "SUCCESS",
            "total_schemes_covered": len(schemes_dossier),
            "consolidated_checklist": list(master_documents.values()),
            "schemes_dossier": schemes_dossier,
            "universal_prerequisites": [
                "1. Aadhaar-NPCI Bank Seeding: Ensure bank account is active on NPCI DBT gateway (check status via UIDAI portal or bank manager).",
                "2. DigiLocker: Fetch digitized copies of Class 10/12 marksheets and Caste/Income certificates for instant e-verification.",
                "3. One Time Registration (OTR): Mandatory on scholarships.gov.in using Aadhaar number and face/OTP authentication."
            ]
        }

        sly_data["documents_generated_count"] = len(master_documents)
        return response

    def _determine_authority(self, doc_name: str, state: str) -> str:
        d = doc_name.lower()
        if "marksheet" in d or "class" in d:
            return "State Board / CBSE / ICSE / DigiLocker"
        if "income" in d:
            if "karnataka" in state:
                return "Nadakacheri / Tahsildar (Karnataka Revenue Dept)"
            elif "andhra" in state:
                return "MeeSeva / Grama Ward Sachivalayam (AP)"
            return "Tahsildar / Sub-Divisional Magistrate / e-District"
        if "caste" in d or "sc" in d or "st" in d:
            if "karnataka" in state:
                return "Nadakacheri (Revenue Dept Karnataka)"
            return "Competent Revenue Authority / Tahsildar"
        if "land" in d:
            if "karnataka" in state:
                return "Bhoomi Portal / Village Accountant (RTC Pahani)"
            return "State Revenue / Land Records Department"
        if "aadhaar" in d:
            return "UIDAI (m-Aadhaar / myaadhaar.uidai.gov.in)"
        if "bank" in d:
            return "Nationalized / Regional Rural / Scheduled Commercial Bank"
        if "otr" in d:
            return "National Scholarship Portal (scholarships.gov.in)"
        if "school" in d or "admission" in d or "institution" in d:
            return "Admitted College / School / University"
        return "Concerned Government / Educational Authority"

    def _get_acquisition_tip(self, doc_name: str, state: str) -> str:
        d = doc_name.lower()
        if "income" in d:
            if "karnataka" in state:
                return "Apply at nadakacheri.karnataka.gov.in -> 15-digit RD Number generated within 7 days."
            return "Apply via State e-District portal or local MeeSeva/CSC with salary slip or affidavit."
        if "caste" in d or "sc" in d or "st" in d:
            return "SC/ST certificates have lifelong validity. Link to DigiLocker for instant OTR pull."
        if "land" in d:
            if "karnataka" in state:
                return "Download digital RTC Pahani from Bhoomi (bhoomojatha.karnataka.gov.in) for ₹15."
            return "Download digitized RoR/Khasra/Pahani from state land records portal."
        if "aadhaar" in d:
            return "Verify bank seeding status at resident.uidai.gov.in/bank-mapper."
        if "marksheet" in d:
            return "Fetch instant tamper-proof digital copy from DigiLocker using Roll Number."
        if "otr" in d:
            return "Download NSP OTR App from Google Play Store for quick biometric e-KYC."
        return "Obtain signed official copy on institution / government letterhead."
