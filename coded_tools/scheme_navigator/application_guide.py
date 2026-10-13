# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
# Scheme Navigator - Step-by-Step Application Guide Generator
# Adapted for official Government of India verified schemes_db.json

from logging import Logger, getLogger
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from neuro_san.interfaces.coded_tool import CodedTool


class ApplicationGuide(CodedTool):
    """
    Provides authoritative, step-by-step application guidance, official portal URLs,
    and verification workflow tips for government schemes.
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
        Generates step-by-step application walkthrough.
        :param args: Dictionary with:
            - scheme_id: Target scheme ID (e.g., "EDU-001", "FARM-001")
        :param sly_data: Dictionary for runtime parameters.
        :return: Comprehensive application roadmap.
        """
        tool_name = self.__class__.__name__
        logger: Logger = getLogger(tool_name)
        logger.info("Generating application guide for: %s", args)

        scheme_id = args.get("scheme_id")
        if not scheme_id:
            guides = []
            for sid, s in self._schemes.items():
                guides.append({
                    "scheme_id": sid,
                    "scheme_name": s.get("name"),
                    "portal_url": s.get("official_application_url"),
                    "category": s.get("category"),
                    "administering_authority": s.get("administering_authority"),
                    "primary_step": s.get("how_to_apply", ["Visit official portal"])[0]
                })
            return {
                "status": "SUCCESS",
                "message": "Specify a scheme_id for full step-by-step instructions.",
                "available_schemes": guides
            }

        scheme = self._schemes.get(scheme_id)
        if not scheme:
            return {
                "status": "NOT_FOUND",
                "error": f"Scheme ID '{scheme_id}' was not found in verified registry.",
                "valid_scheme_ids": list(self._schemes.keys())
            }

        benefits_dict = scheme.get("benefits", {})
        benefit_str = benefits_dict.get("amount") or benefits_dict.get("summary") or "Financial support per scheme guidelines"
        if benefits_dict.get("payment_frequency"):
            benefit_str += f" ({benefits_dict['payment_frequency']})"

        guide_data = {
            "status": "SUCCESS",
            "scheme_id": scheme.get("id"),
            "scheme_name": scheme.get("name"),
            "category": scheme.get("category"),
            "administering_authority": scheme.get("administering_authority"),
            "official_application_url": scheme.get("official_application_url"),
            "official_source_urls": scheme.get("official_source_urls", []),
            "application_status_as_of": scheme.get("application_status_as_of"),
            "benefit_structure": benefit_str,
            "step_by_step_instructions": scheme.get("how_to_apply", []),
            "common_rejection_pitfalls": [
                "Name/DOB mismatch between Aadhaar card and College/Land records. Ensure exact spelling match.",
                "Bank account not active on NPCI DBT gateway (having an account is not enough; DBT mapping must be active).",
                "Delay in School/College Nodal Officer e-verification before the portal deadline.",
                "Expired or unverified Income Certificate. Check financial year validity."
            ],
            "official_verification_notice": f"Always verify announcements on {scheme.get('official_application_url')}. Never pay any fee or bribe to agents; registration on official portals is 100% free."
        }

        sly_data["last_guided_scheme"] = scheme_id
        return guide_data
