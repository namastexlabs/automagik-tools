"""Setup wizard API routes.

Provides endpoints for zero-config setup:
- Check setup status
- Configure local mode
- Configure WorkOS mode
- Validate WorkOS credentials
- Upgrade from local to WorkOS
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from .config_store import ConfigStore
from .mode_manager import (
    AppMode,
    ModeManager,
    LocalModeConfig,
    WorkOSModeConfig,
)

router = APIRouter(prefix="/setup", tags=["setup"])


class SetupStatusResponse(BaseModel):
    """Setup status response."""
    is_setup_required: bool
    current_mode: str
    setup_completed: bool


class LocalModeSetupRequest(BaseModel):
    """Local mode setup request."""
    admin_email: EmailStr = Field(..., description="Admin email address")


class WorkOSModeSetupRequest(BaseModel):
    """WorkOS mode setup request."""
    client_id: str = Field(..., description="WorkOS Client ID", min_length=1)
    api_key: str = Field(..., description="WorkOS API Key", min_length=1)
    authkit_domain: str = Field(..., description="AuthKit domain URL", min_length=1)
    super_admin_emails: list[EmailStr] = Field(
        ...,
        description="Super admin email addresses",
        min_items=1
    )


class WorkOSValidateRequest(BaseModel):
    """WorkOS credentials validation request."""
    client_id: str = Field(..., description="WorkOS Client ID")
    api_key: str = Field(..., description="WorkOS API Key")
    authkit_domain: str = Field(..., description="AuthKit domain URL")


class WorkOSValidateResponse(BaseModel):
    """WorkOS validation response."""
    valid: bool
    error: Optional[str] = None


class SetupSuccessResponse(BaseModel):
    """Setup success response."""
    success: bool
    mode: str
    message: str


async def get_mode_manager(
    session: AsyncSession = Depends(get_db_session)
) -> ModeManager:
    """Dependency to get mode manager."""
    config_store = ConfigStore(session)
    return ModeManager(config_store)


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(
    mode_manager: ModeManager = Depends(get_mode_manager)
):
    """Get setup wizard status.

    Returns:
        Setup status indicating if wizard should be shown
    """
    is_setup_required = await mode_manager.is_setup_required()
    current_mode = await mode_manager.get_current_mode()
    setup_completed = await mode_manager.config_store.is_setup_completed()

    return SetupStatusResponse(
        is_setup_required=is_setup_required,
        current_mode=current_mode.value,
        setup_completed=setup_completed,
    )


@router.post("/local", response_model=SetupSuccessResponse)
async def setup_local_mode(
    request: LocalModeSetupRequest,
    mode_manager: ModeManager = Depends(get_mode_manager)
):
    """Configure local mode (single admin, no password).

    Args:
        request: Local mode configuration

    Returns:
        Setup success response

    Raises:
        HTTPException: If setup fails
    """
    try:
        config = LocalModeConfig(admin_email=request.admin_email)
        await mode_manager.configure_local_mode(config)

        return SetupSuccessResponse(
            success=True,
            mode="local",
            message="Local mode configured successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure local mode: {str(e)}"
        )


@router.post("/workos", response_model=SetupSuccessResponse)
async def setup_workos_mode(
    request: WorkOSModeSetupRequest,
    mode_manager: ModeManager = Depends(get_mode_manager)
):
    """Configure WorkOS mode (enterprise auth).

    Args:
        request: WorkOS mode configuration

    Returns:
        Setup success response

    Raises:
        HTTPException: If setup fails
    """
    try:
        config = WorkOSModeConfig(
            client_id=request.client_id,
            api_key=request.api_key,
            authkit_domain=request.authkit_domain,
            super_admin_emails=request.super_admin_emails,
        )
        await mode_manager.configure_workos_mode(config)

        return SetupSuccessResponse(
            success=True,
            mode="workos",
            message="WorkOS mode configured successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure WorkOS mode: {str(e)}"
        )


@router.post("/workos/validate", response_model=WorkOSValidateResponse)
async def validate_workos_credentials(request: WorkOSValidateRequest):
    """Validate WorkOS credentials before saving.

    Args:
        request: WorkOS credentials to validate

    Returns:
        Validation result

    Note:
        This endpoint tests credentials by making a test API call to WorkOS.
    """
    try:
        # Import WorkOS client
        from workos import WorkOSClient

        # Create client with provided credentials
        client = WorkOSClient(
            api_key=request.api_key,
            client_id=request.client_id,
        )

        # Test API call - list organizations (should work with valid credentials)
        try:
            # This will raise an exception if credentials are invalid
            organizations = client.organizations.list_organizations(limit=1)
            return WorkOSValidateResponse(
                valid=True,
                error=None
            )
        except Exception as api_error:
            return WorkOSValidateResponse(
                valid=False,
                error=f"Invalid credentials: {str(api_error)}"
            )

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="WorkOS client not installed. Run: pip install workos"
        )
    except Exception as e:
        return WorkOSValidateResponse(
            valid=False,
            error=f"Validation error: {str(e)}"
        )


@router.post("/upgrade-to-workos", response_model=SetupSuccessResponse)
async def upgrade_to_workos_mode(
    request: WorkOSModeSetupRequest,
    mode_manager: ModeManager = Depends(get_mode_manager)
):
    """Upgrade from local mode to WorkOS mode.

    Args:
        request: WorkOS mode configuration

    Returns:
        Setup success response

    Raises:
        HTTPException: If not in local mode or upgrade fails
    """
    try:
        config = WorkOSModeConfig(
            client_id=request.client_id,
            api_key=request.api_key,
            authkit_domain=request.authkit_domain,
            super_admin_emails=request.super_admin_emails,
        )
        await mode_manager.upgrade_to_workos(config)

        return SetupSuccessResponse(
            success=True,
            mode="workos",
            message="Upgraded to WorkOS mode successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upgrade to WorkOS mode: {str(e)}"
        )


@router.get("/mode", response_model=dict)
async def get_current_mode(
    mode_manager: ModeManager = Depends(get_mode_manager)
):
    """Get current application mode.

    Returns:
        Current mode and related configuration
    """
    mode = await mode_manager.get_current_mode()
    result = {
        "mode": mode.value,
        "is_configured": mode != AppMode.UNCONFIGURED,
    }

    if mode == AppMode.LOCAL:
        result["admin_email"] = await mode_manager.get_local_admin_email()
    elif mode == AppMode.WORKOS:
        result["super_admin_emails"] = await mode_manager.get_super_admin_emails()
        creds = await mode_manager.get_workos_credentials()
        if creds:
            result["authkit_domain"] = creds["authkit_domain"]

    return result
