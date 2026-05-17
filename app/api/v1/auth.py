"""
Authentication endpoints for signup and API key management.
All endpoints enforce tenant isolation via the get_current_org dependency.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_password_hash, create_access_token
from app.core.security import get_encryption_manager
from app.models.organization import Organization
from app.api.schemas import (
    SignupRequest,
    SignupResponse,
    APIKeyRequest,
    APIKeyResponse,
    OrganizationContext
)
from app.api.dependencies import get_current_org

router = APIRouter()


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new organization and user.
    
    This endpoint:
    - Validates organization name, email, and password
    - Hashes the password using bcrypt
    - Creates a new organization record
    - Issues a JWT access token
    
    Args:
        request: Signup request with organization_name, email, and password
        db: Database session
        
    Returns:
        SignupResponse with access_token, token_type, organization_id, and email
        
    Raises:
        HTTPException: If email already exists (409 Conflict)
    """
    # Check if organization with this email already exists
    existing_org = db.query(Organization).filter(
        Organization.email == request.email
    ).first()
    
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization with this email already exists"
        )
    
    # Hash the password
    password_hash = get_password_hash(request.password)
    
    # Create new organization
    new_organization = Organization(
        name=request.organization_name,
        email=request.email,
        password_hash=password_hash
    )
    
    db.add(new_organization)
    db.commit()
    db.refresh(new_organization)
    
    # Create JWT token
    access_token = create_access_token(
        data={
            "sub": new_organization.email,
            "org_id": str(new_organization.id)
        }
    )
    
    return SignupResponse(
        access_token=access_token,
        token_type="bearer",
        organization_id=str(new_organization.id),
        email=new_organization.email
    )


@router.post("/keys", response_model=APIKeyResponse)
async def add_api_key(
    request: APIKeyRequest,
    org_context: OrganizationContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Add or update an API key for the authenticated organization.
    
    This endpoint:
    - Accepts provider ('openai' or 'anthropic') and admin_api_key
    - Encrypts the API key using Fernet symmetric encryption
    - Stores the encrypted key in the organizations table
    - Enforces tenant isolation by only updating the authenticated org's record
    
    Args:
        request: APIKeyRequest with provider and admin_api_key
        org_context: Organization context from authentication dependency
        db: Database session
        
    Returns:
        APIKeyResponse with success message and provider
    """
    # Get encryption manager
    encryption_manager = get_encryption_manager()
    
    # Encrypt the API key
    encrypted_key = encryption_manager.encrypt(request.admin_api_key)
    
    # Fetch the organization
    organization = db.query(Organization).filter(
        Organization.id == org_context.org_id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update the appropriate encrypted key field based on provider
    if request.provider == 'openai':
        organization.encrypted_openai_admin_key = encrypted_key
    elif request.provider == 'anthropic':
        organization.encrypted_anthropic_admin_key = encrypted_key
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'openai' or 'anthropic'"
        )
    
    db.commit()
    
    return APIKeyResponse(
        message=f"Successfully encrypted and stored {request.provider} API key",
        provider=request.provider
    )
