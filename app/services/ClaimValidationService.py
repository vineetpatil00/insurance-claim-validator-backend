import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from app.models.Claim import ClaimModel
from app.helpers.OCR import extract_text_from_file
from app.services.DataExtraction import DataExtractionService
from app.services.ValidationService import ValidationService
from app.services.VisionService import VisionService
from app.schemas.Claim import (
    ValidationSummary,
    NameValidationResult,
    VehicleValidationResult,
    DateValidationResult,
    DamageDetectionResult,
    DocumentType,
    ExtractedDocumentData,
    ExtractedPolicyData,
    ExtractedClaimFormData,
    ExtractedLicenseData,
    ExtractedKYCData
)

load_dotenv()

class ClaimValidationService:
    """Main service for orchestrating claim validation."""

    def __init__(self):
        self.claim_model = ClaimModel()
        self.data_extraction = DataExtractionService()
        self.validation = ValidationService()
        self.vision = VisionService()
        
        # Create temporary images directory if it doesn't exist
        self.temp_images_dir = Path("temp_images")
        self.temp_images_dir.mkdir(exist_ok=True)

    async def upload_document(
        self,
        claim_id: str,
        document_type: str,
        file_bytes: bytes,
        filename: str
    ) -> Dict:
        """Upload and process a document for a claim."""
        try:
            # Extract text using OCR
            ocr_text = extract_text_from_file(file_bytes, filename)
            
            # Extract structured data using LLM
            extraction_result = await self.data_extraction.extract_data(ocr_text, document_type)
            
            if not extraction_result["success"]:
                return {
                    "success": False,
                    "error": extraction_result.get("error", "Data extraction failed")
                }

            # Get existing claim
            claim = await self.claim_model.get_claim(claim_id)
            if not claim:
                return {
                    "success": False,
                    "error": "Claim not found"
                }

            # Update claim with document data
            documents = claim.get("documents", [])
            document_data = {
                "document_type": document_type,
                "filename": filename,
                "raw_text": ocr_text,
                "extracted_data": extraction_result["data"],
                "confidence": extraction_result.get("confidence", 0.0),
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
            # Check if document type already exists, update it
            existing_idx = None
            for idx, doc in enumerate(documents):
                if doc.get("document_type") == document_type:
                    existing_idx = idx
                    break
            
            if existing_idx is not None:
                documents[existing_idx] = document_data
            else:
                documents.append(document_data)

            await self.claim_model.update_claim(claim_id, {"documents": documents})

            return {
                "success": True,
                "data": {
                    "claim_id": claim_id,
                    "document": ExtractedDocumentData(**document_data).model_dump()
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def upload_image(
        self,
        claim_id: str,
        file_bytes: bytes,
        filename: str,
        angle_description: Optional[str] = None
    ) -> Dict:
        """Upload a car damage image for a claim."""
        try:
            claim = await self.claim_model.get_claim(claim_id)
            if not claim:
                return {
                    "success": False,
                    "error": "Claim not found"
                }

            # Create claim-specific directory
            claim_dir = self.temp_images_dir / claim_id
            claim_dir.mkdir(exist_ok=True)
            
            # Generate unique filename to avoid conflicts
            file_extension = Path(filename).suffix if filename else ".jpg"
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = claim_dir / unique_filename
            
            # Save image to local temporary storage
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            image_data = {
                "filename": filename,
                "angle_description": angle_description,
                "uploaded_at": datetime.utcnow().isoformat(),
                "local_path": str(file_path)  # Store the local file path
            }
            
            # Use atomic push to append image to array (prevents race conditions)
            await self.claim_model.push_to_array(claim_id, "images", image_data)

            return {
                "success": True,
                "data": {
                    "claim_id": claim_id,
                    "image": image_data
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def validate_claim(self, claim_id: str) -> Dict:
        """Perform comprehensive validation on a claim."""
        try:
            claim = await self.claim_model.get_claim(claim_id)
            if not claim:
                return {
                    "success": False,
                    "error": "Claim not found"
                }

            documents = claim.get("documents", [])
            if not documents:
                return {
                    "success": False,
                    "error": "No documents found for validation"
                }

            # Extract data from documents
            policy_data = None
            claim_form_data = None
            license_data = None
            kyc_data = None

            for doc in documents:
                doc_type = doc.get("document_type")
                extracted = doc.get("extracted_data", {})
                
                if doc_type == DocumentType.POLICY:
                    policy_data = ExtractedPolicyData(**extracted)
                elif doc_type == DocumentType.CLAIM_FORM:
                    claim_form_data = ExtractedClaimFormData(**extracted)
                elif doc_type == DocumentType.DRIVING_LICENSE:
                    license_data = ExtractedLicenseData(**extracted)
                elif doc_type in [DocumentType.AADHAAR, DocumentType.PAN]:
                    kyc_data = ExtractedKYCData(**extracted)

            # Perform validations
            # Note: Driving license name is excluded from name validation as driver can be different
            name_validation = self.validation.validate_names(
                policy_name=policy_data.insured_name if policy_data else None,
                claim_form_name=claim_form_data.insured_name if claim_form_data else None,
                license_name=None,  # Excluded - driver can be different from insured
                kyc_name=kyc_data.name if kyc_data else None
            )

            vehicle_validation = self.validation.validate_vehicle(
                policy_data=policy_data,
                claim_form_data=claim_form_data
            )

            date_validation = self.validation.validate_dates(
                policy_data=policy_data,
                claim_form_data=claim_form_data,
                license_data=license_data
            )

            # Vision validation (if images available)
            damage_validation = None
            images = claim.get("images", [])
            if images and claim_form_data:
                try:
                    # Prepare images with bytes for vision analysis
                    images_with_bytes = []
                    
                    for img_data in images:
                        local_path = img_data.get("local_path")
                        if not local_path:
                            # Skip images without local paths
                            continue
                        
                        # Read image bytes from local file
                        file_path = Path(local_path)
                        if file_path.exists():
                            with open(file_path, "rb") as f:
                                image_bytes = f.read()
                            
                            images_with_bytes.append({
                                "bytes": image_bytes,
                                "angle_description": img_data.get("angle_description")
                            })
                    
                    # Only run vision analysis if we have images with bytes
                    if images_with_bytes:
                        damage_validation = await self.vision.analyze_multiple_images(
                            images=images_with_bytes,
                            accident_description=claim_form_data.accident_description,
                            expected_damage_location=claim_form_data.damage_location
                        )
                except Exception as e:
                    # Vision validation failed, but continue with other validations
                    print(f"Vision validation error: {str(e)}")
                    pass

            # Calculate overall validation
            validations = [name_validation, vehicle_validation, date_validation]
            if damage_validation:
                validations.append(damage_validation)

            overall_valid = all(v.is_valid for v in validations if hasattr(v, 'is_valid'))
            overall_confidence = sum(v.confidence for v in validations if hasattr(v, 'confidence')) / len(validations) if validations else 0.0

            # Collect issues and warnings
            issues = []
            warnings = []
            
            if not name_validation.is_valid:
                issues.append(f"Name validation failed: {name_validation.message}")
            if not vehicle_validation.is_valid:
                issues.append(f"Vehicle validation failed: {vehicle_validation.message}")
            if not date_validation.is_valid:
                issues.append(f"Date validation failed: {date_validation.message}")
            if damage_validation and not damage_validation.matches_description:
                warnings.append("Damage in images may not match accident description")

            validation_summary = ValidationSummary(
                overall_valid=overall_valid,
                overall_confidence=overall_confidence,
                name_validation=name_validation,
                vehicle_validation=vehicle_validation,
                date_validation=date_validation,
                damage_validation=damage_validation,
                issues=issues,
                warnings=warnings
            )

            # Update claim with validation results
            await self.claim_model.update_claim(claim_id, {
                "validation": validation_summary.model_dump(),
                "status": "validated"
            })

            return {
                "success": True,
                "data": {
                    "claim_id": claim_id,
                    "validation": validation_summary.model_dump()
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def create_claim(self, data: dict) -> Dict:
        """Create a new claim."""
        try:
            claim_id = await self.claim_model.create_claim(data)
            return {
                "success": True,
                "data": {
                    "claim_id": str(claim_id)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_claim(self, claim_id: str) -> Dict:
        """Get claim details."""
        try:
            claim = await self.claim_model.get_claim(claim_id)
            if not claim:
                return {
                    "success": False,
                    "error": "Claim not found"
                }
            
            claim["_id"] = str(claim["_id"])
            return {
                "success": True,
                "data": claim
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_all_claims(self, skip: int = 0, limit: int = 10) -> Dict:
        """Get all claims with pagination."""
        try:
            claims = await self.claim_model.get_all_claims(skip=skip, limit=limit)
            for claim in claims:
                claim["_id"] = str(claim["_id"])
            
            return {
                "success": True,
                "data": {
                    "claims": claims,
                    "total": len(claims)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

