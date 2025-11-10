import os
import json
from typing import Dict, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.schemas.Claim import (
    ExtractedPolicyData,
    ExtractedClaimFormData,
    ExtractedLicenseData,
    ExtractedKYCData,
    ExtractedRepairEstimateData,
    DocumentType
)

load_dotenv()

class DataExtractionService:
    """Service for extracting structured data from OCR text using LLM."""

    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("Missing GROQ_API_KEY environment variable")
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            groq_api_key=groq_api_key
        )

    async def extract_policy_data(self, ocr_text: str) -> Dict:
        """Extract structured data from policy document OCR text."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting structured data from insurance policy documents.
Extract the following information from the provided OCR text. Return ONLY valid JSON, no markdown or code blocks.

Fields to extract:
- policy_number: Insurance policy number
- policy_start_date: Policy start date (YYYY-MM-DD format if possible)
- policy_expiry_date: Policy expiry date (YYYY-MM-DD format if possible)
- insured_name: Name of the insured person
- vehicle_registration: Vehicle registration number
- chassis_number: Chassis number
- engine_number: Engine number
- make: Vehicle make (e.g., Maruti, Hyundai, Honda)
- model: Vehicle model
- variant: Vehicle variant/version
- color: Vehicle color
- confidence: Your confidence score for this extraction (0.0 to 1.0) based on OCR quality and field completeness

If a field is not found, set it to null. Return valid JSON only."""),
            ("human", "OCR Text:\n{ocr_text}")
        ])

        try:
            response = await self.llm.ainvoke(prompt.format_messages(ocr_text=ocr_text))
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            data = json.loads(content)
            # Extract confidence from LLM response, fallback to 0.0 if not provided
            confidence = data.pop("confidence", 0.0)
            # Ensure confidence is within valid range
            confidence = max(0.0, min(1.0, float(confidence) if confidence is not None else 0.0))
            
            return {
                "success": True,
                "data": ExtractedPolicyData(**data).model_dump(),
                "confidence": confidence
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {},
                "confidence": 0.0
            }

    async def extract_claim_form_data(self, ocr_text: str) -> Dict:
        """Extract structured data from claim form OCR text."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting structured data from insurance claim forms.
Extract the following information from the provided OCR text. Return ONLY valid JSON, no markdown or code blocks.

Fields to extract:
- claim_number: Claim number/reference
- accident_date: Date of accident (YYYY-MM-DD format if possible)
- claim_submission_date: Date when claim was submitted (YYYY-MM-DD format if possible)
- accident_description: Description of the accident
- damage_location: Location of damage (front, rear, left, right, or combination)
- insured_name: Name of the insured person
- vehicle_registration: Vehicle registration number
- confidence: Your confidence score for this extraction (0.0 to 1.0) based on OCR quality and field completeness

If a field is not found, set it to null. Return valid JSON only."""),
            ("human", "OCR Text:\n{ocr_text}")
        ])

        try:
            response = await self.llm.ainvoke(prompt.format_messages(ocr_text=ocr_text))
            content = response.content.strip()
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            data = json.loads(content)
            # Extract confidence from LLM response, fallback to 0.0 if not provided
            confidence = data.pop("confidence", 0.0)
            # Ensure confidence is within valid range
            confidence = max(0.0, min(1.0, float(confidence) if confidence is not None else 0.0))
            
            return {
                "success": True,
                "data": ExtractedClaimFormData(**data).model_dump(),
                "confidence": confidence
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {},
                "confidence": 0.0
            }

    async def extract_license_data(self, ocr_text: str) -> Dict:
        """Extract structured data from driving license OCR text."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting structured data from Indian driving license documents.
Extract the following information from the provided OCR text. Return ONLY valid JSON, no markdown or code blocks.

Fields to extract:
- license_number: Driving license number
- name: Full name as on license
- date_of_birth: Date of birth (YYYY-MM-DD format if possible)
- expiry_date: License expiry date (YYYY-MM-DD format if possible)
- address: Address as on license
- confidence: Your confidence score for this extraction (0.0 to 1.0) based on OCR quality and field completeness

If a field is not found, set it to null. Return valid JSON only."""),
            ("human", "OCR Text:\n{ocr_text}")
        ])

        try:
            response = await self.llm.ainvoke(prompt.format_messages(ocr_text=ocr_text))
            content = response.content.strip()
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            data = json.loads(content)
            # Extract confidence from LLM response, fallback to 0.0 if not provided
            confidence = data.pop("confidence", 0.0)
            # Ensure confidence is within valid range
            confidence = max(0.0, min(1.0, float(confidence) if confidence is not None else 0.0))
            
            return {
                "success": True,
                "data": ExtractedLicenseData(**data).model_dump(),
                "confidence": confidence
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {},
                "confidence": 0.0
            }

    async def extract_kyc_data(self, ocr_text: str, doc_type: str) -> Dict:
        """Extract structured data from Aadhaar or PAN OCR text."""
        doc_name = "Aadhaar" if doc_type == DocumentType.AADHAAR else "PAN"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert at extracting structured data from Indian {doc_name} documents.
Extract the following information from the provided OCR text. Return ONLY valid JSON, no markdown or code blocks.

Fields to extract:
- document_number: {doc_name} number
- name: Full name as on document
- date_of_birth: Date of birth (YYYY-MM-DD format if possible)
- address: Address as on document
- document_type: "{doc_type}"
- confidence: Your confidence score for this extraction (0.0 to 1.0) based on OCR quality and field completeness

If a field is not found, set it to null. Return valid JSON only."""),
            ("human", "OCR Text:\n{ocr_text}")
        ])

        try:
            response = await self.llm.ainvoke(prompt.format_messages(ocr_text=ocr_text))
            content = response.content.strip()
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            data = json.loads(content)
            data["document_type"] = doc_type
            # Extract confidence from LLM response, fallback to 0.0 if not provided
            confidence = data.pop("confidence", 0.0)
            # Ensure confidence is within valid range
            confidence = max(0.0, min(1.0, float(confidence) if confidence is not None else 0.0))
            
            return {
                "success": True,
                "data": ExtractedKYCData(**data).model_dump(),
                "confidence": confidence
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {},
                "confidence": 0.0
            }

    async def extract_repair_estimate_data(self, ocr_text: str) -> Dict:
        """Extract structured data from repair estimate OCR text."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting structured data from vehicle repair estimates.
Extract the following information from the provided OCR text. Return ONLY valid JSON, no markdown or code blocks.

Fields to extract:
- estimate_amount: Total repair estimate amount (numeric value)
- damaged_parts: List of damaged parts/components
- workshop_name: Name of the workshop/garage
- confidence: Your confidence score for this extraction (0.0 to 1.0) based on OCR quality and field completeness

If a field is not found, set it to null. Return valid JSON only."""),
            ("human", "OCR Text:\n{ocr_text}")
        ])

        try:
            response = await self.llm.ainvoke(prompt.format_messages(ocr_text=ocr_text))
            content = response.content.strip()
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            data = json.loads(content)
            # Extract confidence from LLM response, fallback to 0.0 if not provided
            confidence = data.pop("confidence", 0.0)
            # Ensure confidence is within valid range
            confidence = max(0.0, min(1.0, float(confidence) if confidence is not None else 0.0))
            
            return {
                "success": True,
                "data": ExtractedRepairEstimateData(**data).model_dump(),
                "confidence": confidence
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {},
                "confidence": 0.0
            }

    async def extract_data(self, ocr_text: str, document_type: str) -> Dict:
        """Route to appropriate extraction method based on document type."""
        if document_type == DocumentType.POLICY:
            return await self.extract_policy_data(ocr_text)
        elif document_type == DocumentType.CLAIM_FORM:
            return await self.extract_claim_form_data(ocr_text)
        elif document_type == DocumentType.DRIVING_LICENSE:
            return await self.extract_license_data(ocr_text)
        elif document_type in [DocumentType.AADHAAR, DocumentType.PAN]:
            return await self.extract_kyc_data(ocr_text, document_type)
        elif document_type == DocumentType.REPAIR_ESTIMATE:
            return await self.extract_repair_estimate_data(ocr_text)
        else:
            return {
                "success": False,
                "error": f"Unknown document type: {document_type}",
                "data": {},
                "confidence": 0.0
            }

