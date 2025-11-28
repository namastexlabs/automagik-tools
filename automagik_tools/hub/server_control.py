"""Server control API for network configuration and restart.

Provides endpoints to:
- Get running vs saved configuration status
- Apply network configuration changes with restart
- Health check for reconnection polling after restart
"""
import os
import shutil
import subprocess
import time
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from .setup import ConfigStore, get_mode_manager_dep


class ServerStatusResponse(BaseModel):
    """Response showing running config vs saved config."""
    running: dict = Field(description="Currently running configuration")
    saved: dict = Field(description="Saved configuration in database")
    restart_required: bool = Field(description="True if saved differs from running")
    pid: int = Field(description="Current process ID")
    uptime_seconds: float = Field(description="Server uptime in seconds")


class ApplyConfigRequest(BaseModel):
    """Request to apply network configuration."""
    bind_address: str = Field(default="127.0.0.1", description="Bind address (127.0.0.1 or 0.0.0.0)")
    port: int = Field(default=8884, ge=1024, le=65535, description="Port number")


class ApplyConfigResponse(BaseModel):
    """Response after applying configuration."""
    success: bool
    new_url: str = Field(description="URL to connect to after restart")
    restart_method: str = Field(description="Method used: pm2, systemctl, or manual")
    message: str


class HealthResponse(BaseModel):
    """Lightweight health check response."""
    status: str = "ok"
    host: str
    port: int
    uptime_seconds: float


class RestartResult(BaseModel):
    """Result of restart attempt."""
    method: str
    success: bool
    message: str = ""
    instructions: Optional[str] = None


router = APIRouter(prefix="/server", tags=["server"])

# Track server start time for uptime calculation
_server_start_time = time.time()


def get_uptime() -> float:
    """Get server uptime in seconds."""
    return time.time() - _server_start_time


def trigger_restart() -> RestartResult:
    """Restart server using PM2 or systemctl fallback.

    Returns:
        RestartResult with method used and success status
    """
    # Try PM2 first
    pm2 = shutil.which("pm2")
    if pm2:
        try:
            result = subprocess.run(
                [pm2, "restart", "Tools Hub"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return RestartResult(
                    method="pm2",
                    success=True,
                    message="PM2 restart triggered successfully"
                )
            else:
                # PM2 found but restart failed, try with different name
                result = subprocess.run(
                    [pm2, "restart", "automagik-tools"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return RestartResult(
                        method="pm2",
                        success=True,
                        message="PM2 restart triggered successfully"
                    )
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            pass

    # Fallback to systemctl
    systemctl = shutil.which("systemctl")
    if systemctl:
        try:
            result = subprocess.run(
                [systemctl, "restart", "automagik-tools"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return RestartResult(
                    method="systemctl",
                    success=True,
                    message="Systemd restart triggered successfully"
                )
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

    # Manual restart required
    return RestartResult(
        method="manual",
        success=False,
        message="Could not trigger automatic restart",
        instructions="Restart manually: pm2 restart 'Tools Hub' or systemctl restart automagik-tools"
    )


def _trigger_restart_background() -> None:
    """Background task to trigger restart after response is sent."""
    import time
    # Wait a moment for response to be sent
    time.sleep(1)
    trigger_restart()


@router.get("/status", response_model=ServerStatusResponse)
async def get_server_status(mode_manager=Depends(get_mode_manager_dep)):
    """Get running config vs saved config to detect drift.

    Returns current running configuration compared to what's saved in the database.
    If they differ, restart_required will be True.
    """
    try:
        # Get saved config from database
        saved_config = await mode_manager.config_store.get_network_config()

        # Get running config from environment (what was loaded at startup)
        # These are set by the startup wrapper based on database values
        running_host = os.getenv("HUB_HOST", "0.0.0.0")
        running_port = int(os.getenv("HUB_PORT", "8884"))

        running = {
            "bind_address": running_host,
            "port": running_port
        }

        saved = {
            "bind_address": saved_config.get("bind_address", "127.0.0.1"),
            "port": int(saved_config.get("port", 8884))
        }

        # Compare to determine if restart needed
        restart_required = (
            running["bind_address"] != saved["bind_address"] or
            running["port"] != saved["port"]
        )

        return ServerStatusResponse(
            running=running,
            saved=saved,
            restart_required=restart_required,
            pid=os.getpid(),
            uptime_seconds=get_uptime()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting server status: {str(e)}")


@router.post("/apply-config", response_model=ApplyConfigResponse)
async def apply_config(
    request: ApplyConfigRequest,
    background_tasks: BackgroundTasks,
    mode_manager=Depends(get_mode_manager_dep)
):
    """Save config to database and trigger restart.

    This endpoint:
    1. Validates the new configuration
    2. Saves it to the database
    3. Triggers a server restart (PM2 → systemctl → manual fallback)
    4. Returns the new URL for frontend reconnection polling

    The frontend should then poll /api/server/health on the new URL
    until it responds, then redirect.
    """
    try:
        # Validate bind address
        if request.bind_address not in ["127.0.0.1", "0.0.0.0", "localhost"]:
            raise HTTPException(
                status_code=400,
                detail="Bind address must be 127.0.0.1, 0.0.0.0, or localhost"
            )

        # Normalize bind address
        bind_address = request.bind_address
        if bind_address == "localhost":
            bind_address = "127.0.0.1"

        # Save to database
        await mode_manager.config_store.set_network_config({
            "bind_address": bind_address,
            "port": request.port
        })

        # Determine new URL for frontend
        display_host = "localhost" if bind_address == "127.0.0.1" else bind_address
        new_url = f"http://{display_host}:{request.port}"

        # Trigger restart in background (after response is sent)
        background_tasks.add_task(_trigger_restart_background)

        return ApplyConfigResponse(
            success=True,
            new_url=new_url,
            restart_method="background",
            message=f"Configuration saved. Server will restart and be available at {new_url}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying configuration: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health():
    """Lightweight health check for reconnection polling.

    This endpoint is designed to be fast and simple for the frontend
    to poll after a restart to detect when the server is back up.
    """
    # Get current host/port from environment (set by startup wrapper)
    host = os.getenv("HUB_HOST", "0.0.0.0")
    port = int(os.getenv("HUB_PORT", "8884"))

    return HealthResponse(
        status="ok",
        host=host,
        port=port,
        uptime_seconds=get_uptime()
    )


@router.post("/restart")
async def restart_server(background_tasks: BackgroundTasks):
    """Trigger server restart without config changes.

    Useful for applying configuration that was already saved,
    or for general server restart.
    """
    background_tasks.add_task(_trigger_restart_background)

    return {
        "success": True,
        "message": "Server restart triggered. The server will be back shortly."
    }
