"""
FORMGUARD AI - Risk Analysis Engine
Transparent issue prioritization and severity classification.
"""

from typing import Dict, List


class RiskAnalyzer:
    """
    Transparent risk analysis and issue prioritization.
    Does NOT generate arbitrary rejection probabilities.
    """

    # Severity weights for readiness calculation
    SEVERITY_WEIGHTS = {
        "CRITICAL": 0,     # Critical issues mean not ready
        "WARNING": 0.5,    # Warnings are partial credit
        "MANUAL_REVIEW": 0.7,  # Manual review items are mostly ok
        "PASS": 1.0,       # Pass is fully ready
    }

    @staticmethod
    def classify_severity(check_type: str, details: Dict) -> str:
        """
        Classify the severity of a verification finding.

        CRITICAL: Required document missing or confirmed field inconsistency.
        WARNING: Potential problem requiring user attention.
        MANUAL_REVIEW: OCR uncertain or insufficient evidence.
        PASS: Check passed.
        """
        if check_type == "missing_required_document":
            return "CRITICAL"

        if check_type == "name_mismatch":
            similarity = details.get("similarity", 0)
            if similarity < 0.6:
                return "CRITICAL"
            elif similarity < 0.85:
                return "WARNING"
            else:
                return "PASS"

        if check_type == "field_missing":
            is_critical_field = details.get("is_critical_field", False)
            return "WARNING" if is_critical_field else "MANUAL_REVIEW"

        if check_type == "income_exceeds_limit":
            return "WARNING"

        if check_type == "academic_year_mismatch":
            return "WARNING"

        if check_type == "category_mismatch":
            return "WARNING"

        if check_type == "duplicate_document":
            return "WARNING"

        if check_type == "low_ocr_confidence":
            return "MANUAL_REVIEW"

        if check_type == "date_missing":
            return "MANUAL_REVIEW"

        return "MANUAL_REVIEW"

    @staticmethod
    def compute_readiness_score(checks: List[Dict]) -> float:
        """
        Compute an overall readiness percentage.
        This is NOT a rejection probability — it reflects
        how many configured checks have passed.
        """
        if not checks:
            return 0.0

        total_weight = 0
        earned_weight = 0

        for check in checks:
            severity = check.get("severity", "MANUAL_REVIEW")
            weight = RiskAnalyzer.SEVERITY_WEIGHTS.get(severity, 0.5)
            total_weight += 1
            earned_weight += weight

        if total_weight == 0:
            return 0.0

        return round((earned_weight / total_weight) * 100, 1)

    @staticmethod
    def prioritize_issues(checks: List[Dict]) -> List[Dict]:
        """
        Sort issues by priority: CRITICAL first, then WARNING, etc.
        """
        severity_order = {
            "CRITICAL": 0,
            "WARNING": 1,
            "MANUAL_REVIEW": 2,
            "PASS": 3,
        }
        return sorted(
            checks,
            key=lambda c: severity_order.get(c.get("severity", "PASS"), 4)
        )

    @staticmethod
    def generate_summary(checks: List[Dict]) -> Dict:
        """
        Generate a human-readable summary of the verification results.
        """
        pass_count = sum(1 for c in checks if c.get("severity") == "PASS")
        warning_count = sum(1 for c in checks if c.get("severity") == "WARNING")
        critical_count = sum(1 for c in checks if c.get("severity") == "CRITICAL")
        review_count = sum(1 for c in checks if c.get("severity") == "MANUAL_REVIEW")
        total = len(checks)

        readiness = RiskAnalyzer.compute_readiness_score(checks)

        if critical_count > 0:
            status = "Significant issues found that may prevent application processing."
            recommendation = "Address all critical issues before submitting your application."
        elif warning_count > 0:
            status = "Some potential issues found that need your attention."
            recommendation = "Review and address warnings to improve your application readiness."
        elif review_count > 0:
            status = "Application looks good, but some items need manual verification."
            recommendation = "Manually verify the flagged items and confirm the extracted information."
        else:
            status = "All configured checks have passed."
            recommendation = "Your application appears ready for submission. Always verify with official requirements."

        return {
            "total_checks": total,
            "pass_count": pass_count,
            "warning_count": warning_count,
            "critical_count": critical_count,
            "manual_review_count": review_count,
            "readiness_score": readiness,
            "status": status,
            "recommendation": recommendation,
        }
