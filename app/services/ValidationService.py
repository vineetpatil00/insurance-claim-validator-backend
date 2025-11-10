from typing import Dict, List, Optional
from datetime import datetime
from difflib import SequenceMatcher
from app.schemas.Claim import (
    NameValidationResult,
    VehicleValidationResult,
    DateValidationResult,
    ExtractedPolicyData,
    ExtractedClaimFormData,
    ExtractedLicenseData,
    ExtractedKYCData
)

class ValidationService:
    """Service for validating extracted data across documents."""

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize name for comparison (lowercase, remove extra spaces)."""
        if not name:
            return ""
        return " ".join(name.lower().strip().split())

    @staticmethod
    def _name_similarity(name1: str, name2: str) -> float:
        """Calculate similarity between two names (0.0 to 1.0)."""
        if not name1 or not name2:
            return 0.0
        norm1 = ValidationService._normalize_name(name1)
        norm2 = ValidationService._normalize_name(name2)
        return SequenceMatcher(None, norm1, norm2).ratio()

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d-%m-%y",
            "%d/%m/%y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        return None

    def validate_names(
        self,
        policy_name: Optional[str],
        claim_form_name: Optional[str],
        license_name: Optional[str],
        kyc_name: Optional[str]
    ) -> NameValidationResult:
        """Validate that all names match across documents.
        
        Note: Driving license name is excluded from validation as the driver
        can be different from the insured person.
        """
        names = []
        if policy_name:
            names.append(("policy", policy_name))
        if claim_form_name:
            names.append(("claim_form", claim_form_name))
        # Exclude license_name from validation - driver can be different from insured
        # if license_name:
        #     names.append(("license", license_name))
        if kyc_name:
            names.append(("kyc", kyc_name))

        if len(names) < 2:
            return NameValidationResult(
                is_valid=False,
                confidence=0.0,
                matched_names=[],
                message="Insufficient documents for name validation"
            )

        # Compare all pairs
        similarities = []
        mismatches = []
        matched_names = []

        for i, (doc1, name1) in enumerate(names):
            for j, (doc2, name2) in enumerate(names[i+1:], i+1):
                similarity = self._name_similarity(name1, name2)
                similarities.append(similarity)
                
                if similarity >= 0.85:  # High similarity threshold
                    matched_names.append(f"{doc1}: {name1}")
                    matched_names.append(f"{doc2}: {name2}")
                elif similarity < 0.7:  # Low similarity
                    mismatches.append(f"{doc1} ({name1}) vs {doc2} ({name2}): {similarity:.2%}")

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        is_valid = avg_similarity >= 0.80 and len(mismatches) == 0

        return NameValidationResult(
            is_valid=is_valid,
            confidence=avg_similarity,
            matched_names=list(set(matched_names)),
            mismatches=mismatches if mismatches else None,
            message="All names match" if is_valid else f"Name mismatches found: {len(mismatches)}"
        )

    def validate_vehicle(
        self,
        policy_data: Optional[ExtractedPolicyData],
        claim_form_data: Optional[ExtractedClaimFormData]
    ) -> VehicleValidationResult:
        """Validate vehicle information consistency."""
        if not policy_data or not claim_form_data:
            return VehicleValidationResult(
                is_valid=False,
                confidence=0.0,
                message="Missing policy or claim form data for vehicle validation"
            )

        mismatches = []
        checks = []

        # Registration number
        reg_match = False
        if policy_data.vehicle_registration and claim_form_data.vehicle_registration:
            reg_policy = policy_data.vehicle_registration.replace(" ", "").upper()
            reg_claim = claim_form_data.vehicle_registration.replace(" ", "").upper()
            reg_match = reg_policy == reg_claim
            checks.append(reg_match)
            if not reg_match:
                mismatches.append(f"Registration mismatch: {reg_policy} vs {reg_claim}")

        # Chassis number (if available in claim form)
        chassis_match = None
        # Engine number (if available in claim form)
        engine_match = None

        # Make/Model consistency (basic check)
        make_model_match = None
        if policy_data.make and policy_data.model:
            # Could add more sophisticated matching here
            make_model_match = True
            checks.append(True)

        confidence = sum(checks) / len(checks) if checks else 0.0
        is_valid = len(mismatches) == 0 and confidence >= 0.8

        return VehicleValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            registration_match=reg_match if policy_data.vehicle_registration and claim_form_data.vehicle_registration else None,
            chassis_match=chassis_match,
            engine_match=engine_match,
            make_model_match=make_model_match,
            mismatches=mismatches if mismatches else None,
            message="Vehicle information matches" if is_valid else f"Vehicle mismatches: {len(mismatches)}"
        )

    def validate_dates(
        self,
        policy_data: Optional[ExtractedPolicyData],
        claim_form_data: Optional[ExtractedClaimFormData],
        license_data: Optional[ExtractedLicenseData]
    ) -> DateValidationResult:
        """Validate date consistency and logical sequencing."""
        mismatches = []
        checks = []

        # Parse dates
        policy_start = self._parse_date(policy_data.policy_start_date) if policy_data and policy_data.policy_start_date else None
        policy_expiry = self._parse_date(policy_data.policy_expiry_date) if policy_data and policy_data.policy_expiry_date else None
        accident_date = self._parse_date(claim_form_data.accident_date) if claim_form_data and claim_form_data.accident_date else None
        claim_submission = self._parse_date(claim_form_data.claim_submission_date) if claim_form_data and claim_form_data.claim_submission_date else None
        license_expiry = self._parse_date(license_data.expiry_date) if license_data and license_data.expiry_date else None
        current_date = datetime.utcnow()

        # Check for missing dates and add to mismatches
        if policy_data:
            if not policy_data.policy_start_date:
                mismatches.append("Policy start date is missing")
            if not policy_data.policy_expiry_date:
                mismatches.append("Policy expiry date is missing")
        
        if claim_form_data:
            if not claim_form_data.accident_date:
                mismatches.append("Accident date is missing")
            if not claim_form_data.claim_submission_date:
                mismatches.append("Claim submission date is missing")
        
        if license_data and not license_data.expiry_date:
            mismatches.append("License expiry date is missing")

        # Policy date check: Policy Start ≤ Accident Date ≤ Policy Expiry
        policy_date_check = None
        if policy_start and policy_expiry and accident_date:
            if policy_start <= accident_date <= policy_expiry:
                policy_date_check = True
                checks.append(True)
            else:
                policy_date_check = False
                checks.append(False)
                if accident_date < policy_start:
                    mismatches.append(f"Accident date ({accident_date.date()}) is before policy start ({policy_start.date()})")
                elif accident_date > policy_expiry:
                    mismatches.append(f"Accident date ({accident_date.date()}) is after policy expiry ({policy_expiry.date()})")
        elif policy_data and (not policy_start or not policy_expiry or not accident_date):
            # If we have policy data but dates are missing, mark as failed
            policy_date_check = False

        # Claim submission date check: Accident Date ≤ Claim Submission ≤ Current Date
        claim_date_check = None
        if accident_date and claim_submission:
            if accident_date <= claim_submission <= current_date:
                claim_date_check = True
                checks.append(True)
            else:
                claim_date_check = False
                checks.append(False)
                if claim_submission < accident_date:
                    mismatches.append(f"Claim submission ({claim_submission.date()}) is before accident date ({accident_date.date()})")
                elif claim_submission > current_date:
                    mismatches.append(f"Claim submission ({claim_submission.date()}) is in the future")
        elif claim_form_data and accident_date and not claim_submission:
            # If we have claim form and accident date but submission date is missing
            claim_date_check = None  # Can't validate without submission date

        # License expiry check: Accident Date ≤ License Expiry
        license_expiry_check = None
        if accident_date and license_expiry:
            if accident_date <= license_expiry:
                license_expiry_check = True
                checks.append(True)
            else:
                license_expiry_check = False
                checks.append(False)
                mismatches.append(f"License expired before accident: expiry ({license_expiry.date()}) < accident ({accident_date.date()})")
        elif license_data and accident_date and not license_expiry:
            # If we have license data and accident date but expiry is missing
            license_expiry_check = None  # Can't validate without expiry date

        confidence = sum(checks) / len(checks) if checks else 0.0
        # Consider missing dates as validation issues
        is_valid = len(mismatches) == 0 and confidence >= 0.8

        return DateValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            policy_date_check=policy_date_check,
            claim_date_check=claim_date_check,
            license_expiry_check=license_expiry_check,
            mismatches=mismatches if mismatches else None,
            message="All dates are valid" if is_valid else f"Date validation issues: {len(mismatches)}"
        )

