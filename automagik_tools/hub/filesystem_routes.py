"""File system browsing API for setup wizard."""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query

# Project root for security validation
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


class DirectoryEntry(BaseModel):
    """Directory or file entry."""
    name: str
    path: str
    is_directory: bool
    writable: bool = False
    is_git_repo: bool = False


class DirectoryListResponse(BaseModel):
    """Response for directory listing."""
    current_path: str
    parent_path: Optional[str]
    directories: List[DirectoryEntry]
    files: List[DirectoryEntry]


class CreateFolderRequest(BaseModel):
    """Request to create a new folder."""
    path: str


class ValidatePathRequest(BaseModel):
    """Request to validate a path."""
    path: str
    operation: str = "write"  # 'read' or 'write'


class ValidatePathResponse(BaseModel):
    """Response for path validation."""
    valid: bool
    writable: bool = False
    exists: bool = False
    errors: List[str] = []


router = APIRouter(prefix="/api/filesystem", tags=["filesystem"])


def validate_path_security(user_path: str) -> tuple[bool, Optional[str], Optional[Path]]:
    """Validate user-provided path is safe.

    Returns:
        (is_valid, error_message, resolved_path)
    """
    try:
        # Resolve to absolute path, follow symlinks
        abs_path = Path(user_path).resolve()

        # Must be within project root
        try:
            abs_path.relative_to(PROJECT_ROOT)
        except ValueError:
            return False, "Path must be within project directory", None

        # Block system directories
        FORBIDDEN = {'/etc', '/bin', '/sbin', '/usr/bin', '/root', '/sys', '/proc'}
        if str(abs_path) in FORBIDDEN or any(str(abs_path).startswith(f) for f in FORBIDDEN):
            return False, "System directories are not allowed", None

        # Check for directory traversal attempts in original path
        if '..' in user_path:
            return False, "Path traversal not allowed", None

        return True, None, abs_path

    except Exception as e:
        return False, f"Invalid path: {str(e)}", None


def check_writable(path: Path) -> bool:
    """Check if path is writable."""
    try:
        if path.exists():
            return os.access(path, os.W_OK)
        else:
            # Check parent directory
            parent = path.parent
            while not parent.exists() and parent != parent.parent:
                parent = parent.parent
            return os.access(parent, os.W_OK) if parent.exists() else False
    except Exception:
        return False


def is_git_repo(path: Path) -> bool:
    """Check if directory is a git repository."""
    try:
        return (path / ".git").exists()
    except Exception:
        return False


@router.get("/directory", response_model=DirectoryListResponse)
async def list_directory(path: Optional[str] = Query(None, description="Directory path to list")):
    """List directories and files in a given path.

    Security: Only browse within project root, prevent directory traversal.
    """
    # Default to project root if no path provided
    if not path:
        target_path = PROJECT_ROOT
    else:
        is_valid, error, target_path = validate_path_security(path)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

    # Check path exists and is a directory
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    if not target_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    # Check read permissions
    if not os.access(target_path, os.R_OK):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get parent path (None if at root)
    parent_path = None
    if target_path != PROJECT_ROOT:
        try:
            parent_path = str(target_path.parent.relative_to(PROJECT_ROOT))
            if parent_path == ".":
                parent_path = ""
        except ValueError:
            # Parent is outside project root
            parent_path = None

    # List directories and files
    directories = []
    files = []

    try:
        for entry in sorted(target_path.iterdir(), key=lambda x: x.name.lower()):
            # Skip hidden files/directories (except .git)
            if entry.name.startswith('.') and entry.name != '.git':
                continue

            entry_dict = {
                "name": entry.name,
                "path": str(entry.relative_to(PROJECT_ROOT)),
                "is_directory": entry.is_dir(),
                "writable": check_writable(entry),
            }

            if entry.is_dir():
                entry_dict["is_git_repo"] = is_git_repo(entry)
                directories.append(DirectoryEntry(**entry_dict))
            else:
                files.append(DirectoryEntry(**entry_dict))

    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied reading directory")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing directory: {str(e)}")

    return DirectoryListResponse(
        current_path=str(target_path.relative_to(PROJECT_ROOT)) if target_path != PROJECT_ROOT else "",
        parent_path=parent_path,
        directories=directories,
        files=files
    )


@router.post("/create-folder")
async def create_folder(request: CreateFolderRequest):
    """Create a new folder.

    Security: Validate path, check permissions.
    """
    is_valid, error, target_path = validate_path_security(request.path)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Check if already exists
    if target_path.exists():
        raise HTTPException(status_code=400, detail="Path already exists")

    # Check parent directory exists
    if not target_path.parent.exists():
        raise HTTPException(status_code=400, detail="Parent directory does not exist")

    # Check write permissions on parent
    if not check_writable(target_path.parent):
        raise HTTPException(status_code=403, detail="Permission denied: cannot write to parent directory")

    # Create directory
    try:
        target_path.mkdir(parents=False, exist_ok=False)
        return {
            "success": True,
            "path": str(target_path.relative_to(PROJECT_ROOT))
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied creating directory")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating directory: {str(e)}")


@router.post("/validate-path", response_model=ValidatePathResponse)
async def validate_path(request: ValidatePathRequest):
    """Validate a path for read or write operations.

    Returns detailed validation information.
    """
    is_valid, error, target_path = validate_path_security(request.path)

    if not is_valid:
        return ValidatePathResponse(
            valid=False,
            errors=[error] if error else ["Invalid path"]
        )

    errors = []
    exists = target_path.exists() if target_path else False
    writable = check_writable(target_path) if target_path else False

    # Check operation-specific requirements
    if request.operation == "write":
        if not writable:
            errors.append("Path is not writable")
    elif request.operation == "read":
        if exists and not os.access(target_path, os.R_OK):
            errors.append("Path is not readable")

    return ValidatePathResponse(
        valid=len(errors) == 0,
        writable=writable,
        exists=exists,
        errors=errors
    )
