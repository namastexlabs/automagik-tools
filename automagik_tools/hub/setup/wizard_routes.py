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
    # No fields needed - API key is auto-generated
    pass


class WorkOSModeSetupRequest(BaseModel):
    """WorkOS mode setup request."""
    client_id: str = Field(..., description="WorkOS Client ID", min_length=1)
    api_key: str = Field(..., description="WorkOS API Key", min_length=1)
    authkit_domain: str = Field(..., description="AuthKit domain URL", min_length=1)
    super_admin_emails: list[EmailStr] = Field(
        ...,
        description="Super admin email addresses",
        min_length=1
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
    api_key: Optional[str] = None  # Omni API key for local mode
    workspace_id: Optional[str] = None


async def get_mode_manager_dep():
    """Dependency to get mode manager with proper session handling."""
    async with get_db_session() as session:
        config_store = ConfigStore(session)
        yield ModeManager(config_store)


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(
    mode_manager: ModeManager = Depends(get_mode_manager_dep)
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
    mode_manager: ModeManager = Depends(get_mode_manager_dep)
):
    """Configure local mode (single admin, no password).

    Args:
        request: Local mode configuration (empty)

    Returns:
        Setup success response with API key

    Raises:
        HTTPException: If setup fails
    """
    try:
        # Import LocalAuthManager here to avoid circular imports
        from .local_auth import LocalAuthManager

        # Configure local mode and get API key
        config = LocalModeConfig()  # Empty config
        api_key = await mode_manager.configure_local_mode(config)

        # Create local admin user
        async with get_db_session() as session:
            local_auth = LocalAuthManager(session, mode_manager)
            user = await local_auth.get_or_create_local_admin()

        return SetupSuccessResponse(
            success=True,
            mode="local",
            message="Local mode configured successfully",
            api_key=api_key,  # Return API key
            workspace_id=user.workspace_id if user else None,
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
    mode_manager: ModeManager = Depends(get_mode_manager_dep)
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
        This endpoint tests credentials by making a test API call to WorkOS
        AND validates the authkit_domain by checking its OIDC configuration.
    """
    import httpx

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
        except Exception as api_error:
            return WorkOSValidateResponse(
                valid=False,
                error=f"Invalid credentials: {str(api_error)}"
            )

        # Validate authkit_domain by checking OIDC configuration
        # This ensures the domain is reachable and is a valid AuthKit instance
        authkit_domain = request.authkit_domain.rstrip('/')
        oidc_url = f"{authkit_domain}/.well-known/openid-configuration"

        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.get(oidc_url)
                if response.status_code != 200:
                    return WorkOSValidateResponse(
                        valid=False,
                        error=f"AuthKit domain not accessible: HTTP {response.status_code}. "
                              f"Please verify the domain is correct (e.g., https://your-subdomain.authkit.app)"
                    )

                # Verify it's a valid OIDC config with expected issuer
                oidc_config = response.json()
                issuer = oidc_config.get("issuer", "")
                if not issuer.startswith(authkit_domain):
                    return WorkOSValidateResponse(
                        valid=False,
                        error=f"AuthKit domain mismatch: issuer is '{issuer}' but expected '{authkit_domain}'"
                    )

        except httpx.TimeoutException:
            return WorkOSValidateResponse(
                valid=False,
                error="AuthKit domain validation timed out. Please check the domain is correct."
            )
        except httpx.RequestError as e:
            return WorkOSValidateResponse(
                valid=False,
                error=f"Cannot reach AuthKit domain: {str(e)}. Please verify the URL is correct."
            )
        except Exception as e:
            return WorkOSValidateResponse(
                valid=False,
                error=f"AuthKit domain validation failed: {str(e)}"
            )

        return WorkOSValidateResponse(
            valid=True,
            error=None
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
    mode_manager: ModeManager = Depends(get_mode_manager_dep)
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
    mode_manager: ModeManager = Depends(get_mode_manager_dep)
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

    if mode == AppMode.WORKOS:
        result["super_admin_emails"] = await mode_manager.get_super_admin_emails()
        creds = await mode_manager.get_workos_credentials()
        if creds:
            result["authkit_domain"] = creds["authkit_domain"]

    return result


class NetworkConfigRequest(BaseModel):
    """Network configuration request."""
    bind_address: str = Field(..., description="'localhost' or 'network'")
    port: int = Field(..., description="Port number (1024-65535)", ge=1024, le=65535)


class DatabasePathRequest(BaseModel):
    """Database path configuration request."""
    path: str = Field(..., description="Database file path")


@router.post("/network-config")
async def set_network_config(
    request: NetworkConfigRequest,
    mode_manager: ModeManager = Depends(get_mode_manager_dep)
):
    """Set network configuration (bind address and port).

    Args:
        request: Network configuration

    Returns:
        Success response

    Raises:
        HTTPException: If validation fails
    """
    try:
        await mode_manager.config_store.set_network_config(
            request.bind_address,
            request.port
        )
        return {"success": True, "message": "Network configuration saved"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save network configuration: {str(e)}"
        )


@router.post("/database-path")
async def set_database_path(
    request: DatabasePathRequest,
    mode_manager: ModeManager = Depends(get_mode_manager_dep)
):
    """Set database file path.

    Args:
        request: Database path

    Returns:
        Success response

    Raises:
        HTTPException: If path is invalid
    """
    try:
        await mode_manager.config_store.set_database_path(request.path)
        return {"success": True, "message": "Database path saved"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save database path: {str(e)}"
        )


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    mode: Optional[str] = None
    setup_completed: bool
    db_accessible: bool
    error: Optional[str] = None


@router.get("/health", response_model=HealthCheckResponse)
async def get_setup_health():
    """Health check for setup status.

    Returns:
        Health check response with database accessibility and setup status
    """
    try:
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            mode = await config_store.get_app_mode()
            setup_completed = await config_store.is_setup_completed()

        return HealthCheckResponse(
            status="ok",
            mode=mode if mode else None,
            setup_completed=setup_completed,
            db_accessible=True,
        )
    except Exception as e:
        return HealthCheckResponse(
            status="error",
            mode=None,
            setup_completed=False,
            db_accessible=False,
            error=str(e),
        )
