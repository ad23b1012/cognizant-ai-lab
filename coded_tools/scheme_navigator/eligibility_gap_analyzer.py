# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
"""Explain numeric gaps by changing one profile value at a time in the rule engine."""

from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple

from neuro_san.interfaces.coded_tool import CodedTool

from .scheme_eligibility_engine import SchemeEligibilityEngine


class EligibilityGapAnalyzer(CodedTool):
    """Return cautious, single-criterion what-if scenarios for implemented rules."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._engine = SchemeEligibilityEngine()

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        logger = getLogger(self.__class__.__name__)
        scheme_id = args.get("scheme_id")
        if not scheme_id:
            return {"status": "INVALID_INPUT", "message": "scheme_id is required."}

        profile_args = {key: value for key, value in args.items() if key != "scheme_id"}
        profile_args.update({"scheme_id": scheme_id, "domain": "all"})
        baseline = await self._engine.async_invoke(profile_args, sly_data)
        if not isinstance(baseline, dict):
            return {"status": "INVALID_INPUT", "message": "Could not evaluate the supplied profile."}
        if baseline.get("status") in {"INVALID_INPUT", "PRIVATE_INPUT_REQUIRED", "CONSENT_REQUIRED", "NOT_FOUND"}:
            return baseline

        evaluation = next(
            (item for item in baseline.get("eligible_schemes", []) + baseline.get("ineligible_schemes", [])
             if item.get("scheme_id") == scheme_id),
            None,
        )
        if evaluation is None:
            if any(item.get("scheme_id") == scheme_id for item in baseline.get("unsupported_schemes", [])):
                return {
                    "status": "UNSUPPORTED_RULES",
                    "scheme_id": scheme_id,
                    "message": "No what-if analysis is available because this scheme has no implemented eligibility rules.",
                }
            missing = next((item for item in baseline.get("needs_information", []) if item.get("scheme_id") == scheme_id), None)
            return {
                "status": "NEEDS_INFORMATION",
                "scheme_id": scheme_id,
                "missing_fields": missing.get("missing_fields", []) if missing else baseline.get("missing_profile_fields", []),
                "message": "Provide the missing information before calculating a what-if gap.",
            }
        if evaluation["is_eligible"]:
            return {"status": "ALREADY_ELIGIBLE", "scheme_id": scheme_id, "scenarios": []}

        try:
            profile, _ = self._engine._build_effective_profile(profile_args, sly_data)
        except ValueError as exc:
            return {"status": "INVALID_INPUT", "message": str(exc)}
        scheme = next((item for item in self._engine._schemes if item.get("id") == scheme_id), None)
        if not scheme:
            return {"status": "NOT_FOUND", "scheme_id": scheme_id}

        scenarios: List[Dict[str, Any]] = []
        for failure in evaluation.get("rules_audit", []):
            if failure.get("status") != "FAIL":
                continue
            adjustment = self._single_field_adjustment(scheme_id, failure.get("rule", ""), profile)
            if adjustment is None:
                continue
            field, adjusted_value, gap_text = adjustment
            hypothetical = profile.copy()
            hypothetical[field] = adjusted_value
            rerun = self._engine._evaluate_scheme(scheme, hypothetical)
            remaining_failures = [
                rule.get("rule") for rule in rerun.get("rules_audit", [])
                if rule.get("status") == "FAIL" and rule.get("rule") != failure.get("rule")
            ]
            scenarios.append({
                "criterion": failure.get("rule"),
                "gap": gap_text,
                "hypothetical_value": adjusted_value,
                "this_criterion_would_pass": not any(
                    rule.get("rule") == failure.get("rule") and rule.get("status") == "FAIL"
                    for rule in rerun.get("rules_audit", [])
                ),
                "eligible_if_only_this_value_changed": bool(rerun.get("is_eligible")),
                "other_failed_criteria": remaining_failures,
                "caution": "This is a hypothetical rule-engine calculation, not an instruction to alter or misstate official records.",
            })

        logger.info("Built numeric what-if scenarios for scheme %s", scheme_id)
        return {
            "status": "SUCCESS",
            "scheme_id": scheme_id,
            "scheme_name": evaluation.get("scheme_name"),
            "scenarios": scenarios,
            "not_adjustable_by_what_if": [
                item.get("rule") for item in evaluation.get("rules_audit", [])
                if item.get("status") == "FAIL"
                and self._single_field_adjustment(scheme_id, item.get("rule", ""), profile) is None
            ],
            "method": "Each scenario changes one field and reruns the existing deterministic scheme rule evaluator; all other inputs remain fixed.",
            "privacy_note": "Exact private profile values are not returned. Income scenarios disclose only the distance from the applicable ceiling.",
        }

    @staticmethod
    def _single_field_adjustment(
        scheme_id: str, rule: str, profile: Dict[str, Any]
    ) -> Optional[Tuple[str, Any, str]]:
        income_caps = {
            "EDU-001": 450_000, "EDU-002": 350_000, "EDU-003": 800_000,
            "EDU-004": 600_000, "EDU-005": 250_000,
            "AP-EDU-001": 250_000, "AP-EDU-002": 250_000,
        }
        if scheme_id == "KA-EDU-001":
            category = str(profile.get("social_category") or "").upper().replace("_", " ")
            income_caps[scheme_id] = 250_000 if category in {
                "SC", "ST", "SCHEDULED CASTE", "SCHEDULED TRIBE", "CAT-1", "CATEGORY-1", "CAT 1", "CATEGORY 1"
            } else 100_000

        if rule in {"Income Ceiling", "Parental Income"} and scheme_id in income_caps:
            ceiling = income_caps[scheme_id]
            current = profile.get("annual_income_inr")
            if current is not None and current > ceiling:
                gap = current - ceiling
                return (
                    "annual_income_inr", ceiling,
                    f"Reported income is ₹{gap:,.0f} above the applicable ₹{ceiling:,.0f} ceiling; the rule passes at or below the ceiling.",
                )

        if scheme_id == "EDU-001" and rule == "Class XII Merit":
            current = profile.get("class12_percentile")
            if current is not None and current < 80.0:
                return "class12_percentile", 80.0, f"Score is {80.0 - current:g} percentage points below the 80% threshold."

        if scheme_id == "FARM-005" and rule == "Entry Age":
            current = profile.get("age")
            if current is not None:
                target = 18 if current < 18 else 40
                gap = abs(target - current)
                return "age", target, f"Age is {gap} year(s) outside the 18–40 entry window."

        if scheme_id == "FARM-005" and rule == "Landholding Limit":
            current = profile.get("land_acres")
            if current is not None and current > 5.0:
                return "land_acres", 5.0, f"Reported landholding is {current - 5.0:g} acre(s) above the implemented 5-acre limit."

        return None
