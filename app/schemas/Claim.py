from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.PyObjectId import PyObjectId

# Document Types
class DocumentType:
    POLICY = "policy"
    CLAIM_FORM = "claim_form"
    DRIVING_LICENSE = "driving_license"
    AADHAAR = "aadhaar"
    PAN = "pan"
    REPAIR_ESTIMATE = "repair_estimate"

# Extracted Data Schemas
class ExtractedPolicyData(BaseModel):
    policy_number: Optional[str] = None
    policy_start_date: Optional[str] = None
    policy_expiry_date: Optional[str] = None
    insured_name: Optional[str] = None
    vehicle_registration: Optional[str] = None
    chassis_number: Optional[str] = None
    engine_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    color: Optional[str] = None

class ExtractedClaimFormData(BaseModel):
    claim_number: Optional[str] = None
    accident_date: Optional[str] = None
    claim_submission_date: Optional[str] = None
    accident_description: Optional[str] = None
    damage_location: Optional[str] = None  # front, rear, left, right
    insured_name: Optional[str] = None
    vehicle_registration: Optional[str] = None

class ExtractedLicenseData(BaseModel):
    license_number: Optional[str] = None
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    expiry_date: Optional[str] = None
    address: Optional[str] = None

class ExtractedKYCData(BaseModel):
    document_number: Optional[str] = None
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    document_type: Optional[str] = None  # aadhaar or pan

class ExtractedRepairEstimateData(BaseModel):
    estimate_amount: Optional[float] = None
    damaged_parts: Optional[List[str]] = None
    workshop_name: Optional[str] = None

# Validation Result Schemas
class NameValidationResult(BaseModel):
    is_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    matched_names: List[str] = []
    mismatches: Optional[List[str]] = None
    message: str

class VehicleValidationResult(BaseModel):
    is_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    registration_match: Optional[bool] = None
    chassis_match: Optional[bool] = None
    engine_match: Optional[bool] = None
    make_model_match: Optional[bool] = None
    mismatches: Optional[List[str]] = None
    message: str

class DateValidationResult(BaseModel):
    is_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    policy_date_check: Optional[bool] = None
    claim_date_check: Optional[bool] = None
    license_expiry_check: Optional[bool] = None
    mismatches: Optional[List[str]] = None
    message: str

class DamageDetectionResult(BaseModel):
    detected_damage: List[Dict[str, Any]]
    damage_locations: List[str]  # front, rear, left, right
    confidence: float = Field(ge=0.0, le=1.0)
    matches_description: bool
    likely_damaged_parts: List[str]
    unlikely_damaged_parts: Optional[List[str]] = None

class ValidationSummary(BaseModel):
    overall_valid: bool
    overall_confidence: float = Field(ge=0.0, le=1.0)
    name_validation: NameValidationResult
    vehicle_validation: VehicleValidationResult
    date_validation: DateValidationResult
    damage_validation: Optional[DamageDetectionResult] = None
    issues: List[str] = []
    warnings: List[str] = []

# Request/Response Schemas
class DocumentUploadRequest(BaseModel):
    document_type: str
    filename: str

class ImageUploadRequest(BaseModel):
    filename: str
    angle_description: Optional[str] = None  # front, rear, left, right, etc.

class ClaimValidationRequest(BaseModel):
    claim_id: str

class ClaimCreateRequest(BaseModel):
    claim_number: Optional[str] = None
    description: Optional[str] = None

class ExtractedDocumentData(BaseModel):
    document_type: str
    raw_text: str
    extracted_data: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)

class ClaimResponse(BaseModel):
    claim_id: str
    claim_number: Optional[str] = None
    status: str
    documents: List[ExtractedDocumentData] = []
    images: List[str] = []
    validation: Optional[ValidationSummary] = None
    created_on: datetime
    updated_on: Optional[datetime] = None

