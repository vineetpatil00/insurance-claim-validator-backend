from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from app.services.ClaimValidationService import ClaimValidationService
from app.schemas.ServerResponse import ServerResponse
from app.helpers.Utilities import Utils
from app.schemas.Claim import DocumentType

router = APIRouter(prefix="/api/v1/claims", tags=["Claims"])

def get_claim_service():
    return ClaimValidationService()


@router.post("/create", response_model=ServerResponse)
async def create_claim(
    claim_number: str = Form(None),
    description: str = Form(None),
    service: ClaimValidationService = Depends(get_claim_service)
):
    """Create a new insurance claim."""
    try:
        data = {
            "claim_number": claim_number,
            "description": description,
            "status": "draft",
            "documents": [],
            "images": []
        }
        result = await service.create_claim(data)
        return Utils.create_response(
            data=result.get("data"),
            success=result.get("success", False),
            error=result.get("error", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"data": None, "error": str(e), "success": False}
        )


@router.post("/{claim_id}/documents", response_model=ServerResponse)
async def upload_document(
    claim_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    service: ClaimValidationService = Depends(get_claim_service)
):
    """
    Upload a document for claim validation.
    
    Supported document types: policy, claim_form, driving_license, aadhaar, pan, repair_estimate
    """
    try:
        # Validate document type
        valid_types = [
            DocumentType.POLICY,
            DocumentType.CLAIM_FORM,
            DocumentType.DRIVING_LICENSE,
            DocumentType.AADHAAR,
            DocumentType.PAN,
            DocumentType.REPAIR_ESTIMATE
        ]
        if document_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
            )

        # Read file bytes
        file_bytes = await file.read()
        
        result = await service.upload_document(
            claim_id=claim_id,
            document_type=document_type,
            file_bytes=file_bytes,
            filename=file.filename
        )
        
        return Utils.create_response(
            data=result.get("data"),
            success=result.get("success", False),
            error=result.get("error", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"data": None, "error": str(e), "success": False}
        )


@router.post("/{claim_id}/images", response_model=ServerResponse)
async def upload_image(
    claim_id: str,
    file: UploadFile = File(...),
    angle_description: str = Form(None),
    service: ClaimValidationService = Depends(get_claim_service)
):
    """
    Upload a car damage image for claim validation.
    
    angle_description: Optional description of image angle (e.g., "front", "rear", "left", "right")
    """
    try:
        # Read file bytes
        file_bytes = await file.read()
        
        result = await service.upload_image(
            claim_id=claim_id,
            file_bytes=file_bytes,
            filename=file.filename,
            angle_description=angle_description
        )
        
        return Utils.create_response(
            data=result.get("data"),
            success=result.get("success", False),
            error=result.get("error", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"data": None, "error": str(e), "success": False}
        )


@router.post("/{claim_id}/validate", response_model=ServerResponse)
async def validate_claim(
    claim_id: str,
    service: ClaimValidationService = Depends(get_claim_service)
):
    """
    Perform comprehensive validation on a claim.
    
    Validates:
    - Name consistency across all documents
    - Vehicle information consistency
    - Date logical sequencing
    - Damage detection from images (if available)
    """
    try:
        result = await service.validate_claim(claim_id)
        return Utils.create_response(
            data=result.get("data"),
            success=result.get("success", False),
            error=result.get("error", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"data": None, "error": str(e), "success": False}
        )


@router.get("/{claim_id}", response_model=ServerResponse)
async def get_claim(
    claim_id: str,
    service: ClaimValidationService = Depends(get_claim_service)
):
    """Get claim details by ID."""
    try:
        result = await service.get_claim(claim_id)
        return Utils.create_response(
            data=result.get("data"),
            success=result.get("success", False),
            error=result.get("error", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"data": None, "error": str(e), "success": False}
        )


@router.get("/", response_model=ServerResponse)
async def get_all_claims(
    skip: int = Query(default=0, ge=0, description="Pagination skip count"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of claims to fetch"),
    service: ClaimValidationService = Depends(get_claim_service)
):
    """Get all claims with pagination."""
    try:
        result = await service.get_all_claims(skip=skip, limit=limit)
        return Utils.create_response(
            data=result.get("data"),
            success=result.get("success", False),
            error=result.get("error", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"data": None, "error": str(e), "success": False}
        )

