"""
FastAPI dependencies for authentication and authorization.
Provides reusable dependency injection for protected routes.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import decode_access_token
from app.models.organization import Organization
from app.api.schemas import OrganizationContext

# HTTPBearer security scheme for Bearer token authentication
security = HTTPBearer(auto_error=False)


async def get_current_org(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> OrganizationContext:
    """
    FastAPI dependency to authenticate and extract organization context.
    
    This dependency:
    1. Extracts the JWT from the Authorization header
    2. Validates the token signature and expiration
    3. Decodes claims (sub for email, org_id for organization)
    4. Verifies the organization exists in the database
    5. Injects OrganizationContext into protected routes
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session dependency
        
    Returns:
        OrganizationContext with org_id and email
        
    Raises:
        HTTPException: If authentication fails (401 Unauthorized)
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Decode and validate the JWT token
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract claims
    email: str = payload.get("sub")
    org_id: str = payload.get("org_id")
    
    if email is None or org_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify organization exists in database
    organization = db.query(Organization).filter(
        Organization.id == org_id,
        Organization.email == email
    ).first()
    
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Organization not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return organization context
    return OrganizationContext(
        org_id=str(organization.id),
        email=organization.email
    )
