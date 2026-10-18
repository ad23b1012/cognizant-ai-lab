# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
"""Pre-submission checks for common document and payment rejection risks."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from neuro_san.interfaces.coded_tool import CodedTool


class ApplicationReadinessChecker(CodedTool):
    """Ask for yes/no/not-sure checks and return actionable application risks."""

    ANSWERS = {"yes", "no", "not_sure"}

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._schemes = self._load_schemes()

    @staticmethod
    def _locate_db() -> Path:
        return Path(__file__).resolve().parent.parent.parent / "data" / "schemes_db.json"

    def _load_schemes(self) -> Dict[str, Dict[str, Any]]:
        path = self._locate_db()
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as stream:
            return {scheme["id"]: scheme for scheme in json.load(stream).get("schemes", [])}

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        logger = logging.getLogger(self.__class__.__name__)
        scheme_id = args.get("scheme_id")
        scheme = self._schemes.get(scheme_id)
        if not scheme:
            return {"status": "NOT_FOUND", "message": "Provide a valid scheme_id from the scheme registry."}

        education_scheme = "education" in str(scheme.get("category", "")).lower()
        question_specs = [
            ("name_matches_documents", "Do your name and date of birth match across Aadhaar (if used) and your application documents?", "Correct mismatches with the issuing authority before submitting."),
            ("dbt_ready", "Is the receiving bank account active and Aadhaar/NPCI DBT mapped, if this scheme pays by DBT?", "Ask your bank to verify that the account is active and its Aadhaar/NPCI DBT mapping is enabled."),
            ("required_certificates_ready", "Do you have the required certificates and supporting documents for this scheme?", "Use the official checklist to obtain missing documents from the listed authority, such as Nadakacheri or MeeSeva where applicable."),
            ("certificates_current", "Are any time-limited certificates required for this scheme valid for the current application period?", "Confirm validity periods on the official portal; obtain a current certificate if needed."),
        ]
        if education_scheme:
            question_specs.append((
                "institution_verified",
                "Has your school/college nodal officer completed or confirmed the required application verification?",
                "Contact your institution's scholarship nodal officer and confirm verification before the portal deadline.",
            ))

        answers = args.get("answers", {}) or {}
        if not isinstance(answers, dict):
            return {"status": "INVALID_INPUT", "message": "answers must be an object of yes/no/not_sure values."}
        normalized: Dict[str, str] = {}
        for key, answer in answers.items():
            value = str(answer).strip().lower().replace(" ", "_")
            if key not in {spec[0] for spec in question_specs} or value not in self.ANSWERS:
                return {
                    "status": "INVALID_INPUT",
                    "message": "Use only applicable check names and answer each with yes, no, or not_sure.",
                }
            normalized[key] = value

        missing = [spec for spec in question_specs if spec[0] not in normalized]
        if missing:
            field, question, _ = missing[0]
            return {
                "status": "NEEDS_ANSWERS",
                "scheme_id": scheme_id,
                "scheme_name": scheme.get("name"),
                "next_question": {"field": field, "question": question, "options": ["Yes", "No", "Not sure"]},
                "remaining_questions": len(missing),
                "instruction": "Ask this one question, wait for the citizen's answer, then call again with the accumulated answers.",
            }

        risks: List[Dict[str, str]] = []
        for field, question, fix in question_specs:
            answer = normalized[field]
            if answer == "yes":
                continue
            risks.append({
                "check": field,
                "answer": answer,
                "priority": "action_needed" if answer == "no" else "verify_before_submission",
                "risk": question,
                "how_to_reduce_risk": fix,
            })

        result = {
            "status": "REVIEW_REQUIRED" if risks else "READY_FOR_FINAL_REVIEW",
            "scheme_id": scheme_id,
            "scheme_name": scheme.get("name"),
            "risk_count": len(risks),
            "risks": risks,
            "message": "Resolve or verify the listed items before submission." if risks else "All pre-check answers are affirmative. Review the official portal checklist and deadline before submitting.",
            "disclaimer": "This is a practical pre-check, not an official rejection prediction or guarantee of acceptance.",
        }
        logger.info("Completed application readiness pre-check for %s with %d flagged items", scheme_id, len(risks))
        return result
