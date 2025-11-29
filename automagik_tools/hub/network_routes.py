"""Network configuration API for setup wizard."""
import asyncio
import os
import socket
import psutil
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException


class NetworkInterface(BaseModel):
    """Network interface information."""
    name: str
    address: str
    type: str  # 'loopback', 'ethernet', 'wifi', etc.


class NetworkInfoResponse(BaseModel):
    """Response for network information."""
    interfaces: List[NetworkInterface]
    hostname: str
    recommended_bind: str


class TestPortRequest(BaseModel):
    """Request to test port availability."""
    port: int


class PortConflict(BaseModel):
    """Information about a process using a port."""
    pid: int
    process: str
    command: Optional[str] = None
    is_self: bool = False  # True if this is our server process


class TestPortResponse(BaseModel):
    """Response for port availability test."""
    available: bool
    port: int
    conflicts: List[PortConflict] = []
    suggestions: List[int] = []


router = APIRouter(prefix="/network", tags=["network"])


def get_network_interfaces() -> List[NetworkInterface]:
    """Get all network interfaces with their addresses."""
    interfaces = []

    for interface_name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            # Only interested in IPv4 addresses
            if addr.family == socket.AF_INET:
                # Determine interface type
                if interface_name.startswith('lo'):
                    if_type = 'loopback'
                elif interface_name.startswith(('eth', 'en')):
                    if_type = 'ethernet'
                elif interface_name.startswith('wl'):
                    if_type = 'wifi'
                else:
                    if_type = 'other'

                interfaces.append(NetworkInterface(
                    name=interface_name,
                    address=addr.address,
                    type=if_type
                ))

    return interfaces


def is_port_in_use(port: int) -> tuple[bool, List[PortConflict]]:
    """Check if a port is in use and get process information.

    Returns:
        (is_in_use, conflicts)
    """
    conflicts = []
    current_pid = os.getpid()  # Our server's PID for self-detection

    try:
        # Get all connections
        connections = psutil.net_connections(kind='inet')

        for conn in connections:
            if conn.laddr.port == port:
                # Skip connections where PID is unavailable (common on Linux/WSL)
                if conn.pid is None:
                    continue
                # Port is in use - check if it's ourselves
                is_self = (conn.pid == current_pid)
                try:
                    process = psutil.Process(conn.pid)
                    conflicts.append(PortConflict(
                        pid=conn.pid,
                        process=process.name(),
                        command=' '.join(process.cmdline()[:3]) if process.cmdline() else None,
                        is_self=is_self,
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    conflicts.append(PortConflict(
                        pid=conn.pid,
                        process="unknown",
                        command=None,
                        is_self=is_self,
                    ))

        return len(conflicts) > 0, conflicts

    except (PermissionError, psutil.AccessDenied):
        # Fallback: try to bind to port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return False, []
        except OSError:
            return True, []


async def suggest_alternative_ports(port: int, count: int = 3) -> List[int]:
    """Suggest alternative ports based on the requested port.

    Uses memorable prefix pattern (like email suggestions):
    8000 -> 18000, 28000, 38000
    """
    suggestions = []

    # Gmail-style: prefix the port with 1, 2, 3...
    # e.g., 8000 -> 18000, 28000, 38000
    for prefix in range(1, 10):
        candidate = int(f"{prefix}{port}")
        if 1024 <= candidate <= 65535:
            in_use, _ = is_port_in_use(candidate)
            if not in_use:
                suggestions.append(candidate)
                if len(suggestions) >= count:
                    return suggestions

    # Fallback to sequential if prefixed ports all taken
    for offset in range(1, 50):
        candidate = port + offset
        if 1024 <= candidate <= 65535:
            in_use, _ = is_port_in_use(candidate)
            if not in_use:
                suggestions.append(candidate)
                if len(suggestions) >= count:
                    return suggestions

    return suggestions


@router.get("/info", response_model=NetworkInfoResponse)
async def get_network_info():
    """Get network interface information.

    Returns list of available network interfaces with IPs.
    """
    try:
        interfaces = get_network_interfaces()
        hostname = socket.gethostname()

        # Recommend localhost by default for security
        recommended_bind = "127.0.0.1"

        return NetworkInfoResponse(
            interfaces=interfaces,
            hostname=hostname,
            recommended_bind=recommended_bind
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting network info: {str(e)}")


@router.post("/test-port", response_model=TestPortResponse)
async def test_port(request: TestPortRequest):
    """Test if a port is available.

    Returns availability status and alternative suggestions if in use.
    """
    port = request.port

    # Validate port range
    if not (1024 <= port <= 65535):
        raise HTTPException(
            status_code=400,
            detail="Port must be between 1024 and 65535 (privileged ports <1024 not allowed)"
        )

    try:
        in_use, conflicts = is_port_in_use(port)

        if in_use:
            # Port is in use, suggest alternatives (parallelized for speed)
            suggestions = await suggest_alternative_ports(port)

            return TestPortResponse(
                available=False,
                port=port,
                conflicts=conflicts,
                suggestions=suggestions
            )
        else:
            # Port is available
            return TestPortResponse(
                available=True,
                port=port,
                conflicts=[],
                suggestions=[]
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing port: {str(e)}")
