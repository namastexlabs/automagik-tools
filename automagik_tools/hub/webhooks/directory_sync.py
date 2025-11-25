"""Directory Sync webhook handler.

Handles WorkOS Directory Sync webhooks for Google Workspace user provisioning.

Events handled:
- dsync.user.created: New user in Google Workspace
- dsync.user.updated: User attributes changed
- dsync.user.deleted: User removed from directory
- dsync.group.created: New group created
- dsync.group.updated: Group attributes changed
- dsync.group.deleted: Group removed
- dsync.group.user_added: User added to group
- dsync.group.user_removed: User removed from group

Webhook Setup in WorkOS Dashboard:
1. Navigate to Directory Sync → Webhooks
2. Add endpoint: https://your-hub.com/webhooks/workos/directory-sync
3. Copy the signing secret to WORKOS_WEBHOOK_SECRET env var
"""
import os
import hmac
import hashlib
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
from sqlalchemy import select

from ..database import get_db_session
from ..models import (
    User, Workspace, DirectorySyncUser, DirectoryGroup,
    DirectoryGroupMembership, UserRole, ProvisioningMethod, AuditLog, AuditEventCategory
)
from ..authorization import generate_workspace_slug, is_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/workos", tags=["webhooks"])

# Webhook signing secret from environment
WEBHOOK_SECRET = os.getenv("WORKOS_WEBHOOK_SECRET", "")


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    timestamp: str,
) -> bool:
    """Verify WorkOS webhook signature.

    WorkOS uses HMAC-SHA256 for webhook signatures.
    Signature format: t=timestamp,v1=signature

    Args:
        payload: Raw request body
        signature: WorkOS-Signature header value
        timestamp: Timestamp from signature

    Returns:
        True if signature is valid
    """
    if not WEBHOOK_SECRET:
        logger.warning("WORKOS_WEBHOOK_SECRET not configured, skipping verification")
        return True  # Allow in dev, but log warning

    # Parse signature header
    # Format: t=1234567890,v1=abc123...
    parts = {}
    for part in signature.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            parts[key] = value

    if "t" not in parts or "v1" not in parts:
        return False

    # Compute expected signature
    # signed_payload = timestamp + "." + payload
    signed_payload = f"{parts['t']}.{payload.decode('utf-8')}"
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(expected_signature, parts["v1"])


@router.post("/directory-sync")
async def handle_directory_sync(
    request: Request,
    background_tasks: BackgroundTasks,
    workos_signature: str = Header(None, alias="WorkOS-Signature"),
):
    """Handle Directory Sync webhook events from WorkOS.

    This endpoint receives events when users are added/removed/updated
    in the connected Google Workspace directory.

    Returns 200 OK immediately to acknowledge receipt, then processes
    the event in the background.
    """
    # Get raw payload for signature verification
    payload = await request.body()

    # Verify signature (skip in dev if secret not set)
    if WEBHOOK_SECRET and workos_signature:
        if not verify_webhook_signature(payload, workos_signature, ""):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("event")
    event_data = event.get("data", {})
    event_id = event.get("id", str(uuid.uuid4()))

    logger.info(f"Received Directory Sync event: {event_type} (id={event_id})")

    # Process event in background to return 200 quickly
    background_tasks.add_task(process_directory_sync_event, event_type, event_data, event_id)

    return {"received": True, "event_id": event_id}


async def process_directory_sync_event(
    event_type: str,
    event_data: Dict[str, Any],
    event_id: str,
):
    """Process Directory Sync event in background.

    Args:
        event_type: WorkOS event type (e.g., "dsync.user.created")
        event_data: Event payload data
        event_id: Unique event ID
    """
    try:
        if event_type == "dsync.user.created":
            await handle_user_created(event_data)
        elif event_type == "dsync.user.updated":
            await handle_user_updated(event_data)
        elif event_type == "dsync.user.deleted":
            await handle_user_deleted(event_data)
        elif event_type == "dsync.group.created":
            await handle_group_created(event_data)
        elif event_type == "dsync.group.updated":
            await handle_group_updated(event_data)
        elif event_type == "dsync.group.deleted":
            await handle_group_deleted(event_data)
        elif event_type == "dsync.group.user_added":
            await handle_group_user_added(event_data)
        elif event_type == "dsync.group.user_removed":
            await handle_group_user_removed(event_data)
        else:
            logger.warning(f"Unknown Directory Sync event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing Directory Sync event {event_type}: {e}", exc_info=True)


async def handle_user_created(data: Dict[str, Any]):
    """Handle dsync.user.created event.

    Creates a new user in the Hub with their own workspace.

    Args:
        data: User data from WorkOS
    """
    directory_user = data.get("directory_user", data)

    dsync_user_id = directory_user.get("id")
    directory_id = directory_user.get("directory_id")
    email = directory_user.get("emails", [{}])[0].get("value", "")
    first_name = directory_user.get("first_name", "")
    last_name = directory_user.get("last_name", "")
    idp_id = directory_user.get("idp_id", "")
    state = directory_user.get("state", "active")

    if not email:
        logger.error(f"Directory Sync user has no email: {dsync_user_id}")
        return

    logger.info(f"Creating user from Directory Sync: {email}")

    async with get_db_session() as session:
        # Check if DirectorySyncUser already exists
        result = await session.execute(
            select(DirectorySyncUser).where(DirectorySyncUser.id == dsync_user_id)
        )
        existing_dsync_user = result.scalar_one_or_none()

        if existing_dsync_user:
            logger.info(f"Directory Sync user already exists: {dsync_user_id}")
            return

        # Check if User already exists by email
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Link existing user to Directory Sync
            existing_user.directory_sync_id = dsync_user_id
            existing_user.idp_id = idp_id
            existing_user.provisioned_via = ProvisioningMethod.DIRECTORY_SYNC.value
            user = existing_user
        else:
            # Create new user
            user_id = str(uuid.uuid4())
            user = User(
                id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.WORKSPACE_OWNER.value,
                is_super_admin=is_super_admin(email),
                directory_sync_id=dsync_user_id,
                idp_id=idp_id,
                provisioned_via=ProvisioningMethod.DIRECTORY_SYNC.value,
                mfa_grace_period_end=datetime.utcnow() + timedelta(days=7),
            )
            session.add(user)
            await session.flush()

            # Create workspace for new user
            workspace_name = f"{first_name or email.split('@')[0]}'s Workspace"
            result = await session.execute(select(Workspace.slug))
            existing_slugs = [row[0] for row in result.fetchall()]
            slug = generate_workspace_slug(workspace_name, existing_slugs)

            workspace = Workspace(
                id=str(uuid.uuid4()),
                name=workspace_name,
                slug=slug,
                owner_id=user.id,
                settings={"default_tools": [], "mfa_required": True},
            )
            session.add(workspace)
            await session.flush()

            user.workspace_id = workspace.id

        # Create DirectorySyncUser record
        dsync_user = DirectorySyncUser(
            id=dsync_user_id,
            directory_id=directory_id,
            user_id=user.id,
            idp_id=idp_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            state=state,
            raw_data=directory_user,
        )
        session.add(dsync_user)

        # Log audit event
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            workspace_id=user.workspace_id,
            action="admin.user_provisioned",
            category=AuditEventCategory.ADMIN.value,
            actor_type="system",
            target_type="user",
            target_id=user.id,
            target_name=email,
            event_metadata={"source": "directory_sync", "directory_id": directory_id},
            success=True,
        )
        session.add(audit_log)

        await session.commit()

    logger.info(f"User created from Directory Sync: {email}")


async def handle_user_updated(data: Dict[str, Any]):
    """Handle dsync.user.updated event.

    Updates user attributes (name, state, etc.).
    """
    directory_user = data.get("directory_user", data)

    dsync_user_id = directory_user.get("id")
    email = directory_user.get("emails", [{}])[0].get("value", "")
    first_name = directory_user.get("first_name", "")
    last_name = directory_user.get("last_name", "")
    state = directory_user.get("state", "active")

    logger.info(f"Updating user from Directory Sync: {email} (state={state})")

    async with get_db_session() as session:
        # Find DirectorySyncUser
        result = await session.execute(
            select(DirectorySyncUser).where(DirectorySyncUser.id == dsync_user_id)
        )
        dsync_user = result.scalar_one_or_none()

        if not dsync_user:
            logger.warning(f"Directory Sync user not found: {dsync_user_id}")
            return

        # Update DirectorySyncUser
        dsync_user.first_name = first_name
        dsync_user.last_name = last_name
        dsync_user.state = state
        dsync_user.raw_data = directory_user
        dsync_user.updated_at = datetime.utcnow()

        # Update linked User if exists
        if dsync_user.user_id:
            result = await session.execute(
                select(User).where(User.id == dsync_user.user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.first_name = first_name
                user.last_name = last_name
                user.updated_at = datetime.utcnow()

                # If user is suspended in directory, we could disable them here
                # For now, just log it

        await session.commit()

    logger.info(f"User updated from Directory Sync: {email}")


async def handle_user_deleted(data: Dict[str, Any]):
    """Handle dsync.user.deleted event.

    When a user is removed from the directory:
    - Mark DirectorySyncUser as deleted
    - Optionally: Disable user account (configurable)

    Note: We don't delete user data immediately to allow for recovery.
    """
    directory_user = data.get("directory_user", data)
    dsync_user_id = directory_user.get("id")

    logger.info(f"User deleted from Directory Sync: {dsync_user_id}")

    async with get_db_session() as session:
        result = await session.execute(
            select(DirectorySyncUser).where(DirectorySyncUser.id == dsync_user_id)
        )
        dsync_user = result.scalar_one_or_none()

        if dsync_user:
            dsync_user.state = "deleted"
            dsync_user.updated_at = datetime.utcnow()

            # Log audit event
            if dsync_user.user_id:
                result = await session.execute(
                    select(User).where(User.id == dsync_user.user_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    audit_log = AuditLog(
                        id=str(uuid.uuid4()),
                        workspace_id=user.workspace_id,
                        action="admin.user_deprovisioned",
                        category=AuditEventCategory.ADMIN.value,
                        actor_type="system",
                        target_type="user",
                        target_id=user.id,
                        target_name=dsync_user.email,
                        event_metadata={"source": "directory_sync"},
                        success=True,
                    )
                    session.add(audit_log)

            await session.commit()

    logger.info(f"User marked as deleted: {dsync_user_id}")


async def handle_group_created(data: Dict[str, Any]):
    """Handle dsync.group.created event."""
    directory_group = data.get("directory_group", data)

    group_id = directory_group.get("id")
    directory_id = directory_group.get("directory_id")
    name = directory_group.get("name", "")
    idp_id = directory_group.get("idp_id")

    logger.info(f"Creating group from Directory Sync: {name}")

    async with get_db_session() as session:
        group = DirectoryGroup(
            id=group_id,
            directory_id=directory_id,
            name=name,
            idp_id=idp_id,
            raw_data=directory_group,
        )
        session.add(group)
        await session.commit()

    logger.info(f"Group created: {name}")


async def handle_group_updated(data: Dict[str, Any]):
    """Handle dsync.group.updated event."""
    directory_group = data.get("directory_group", data)

    group_id = directory_group.get("id")
    name = directory_group.get("name", "")

    logger.info(f"Updating group from Directory Sync: {name}")

    async with get_db_session() as session:
        result = await session.execute(
            select(DirectoryGroup).where(DirectoryGroup.id == group_id)
        )
        group = result.scalar_one_or_none()

        if group:
            group.name = name
            group.raw_data = directory_group
            group.updated_at = datetime.utcnow()
            await session.commit()


async def handle_group_deleted(data: Dict[str, Any]):
    """Handle dsync.group.deleted event."""
    directory_group = data.get("directory_group", data)
    group_id = directory_group.get("id")

    logger.info(f"Deleting group from Directory Sync: {group_id}")

    async with get_db_session() as session:
        result = await session.execute(
            select(DirectoryGroup).where(DirectoryGroup.id == group_id)
        )
        group = result.scalar_one_or_none()

        if group:
            await session.delete(group)
            await session.commit()


async def handle_group_user_added(data: Dict[str, Any]):
    """Handle dsync.group.user_added event.

    When a user is added to a group, we can optionally:
    - Grant additional permissions
    - Add to team workspace (future feature)
    """
    directory_group = data.get("directory_group", data)
    directory_user = data.get("directory_user", {})

    group_id = directory_group.get("id")
    user_id = directory_user.get("id")

    logger.info(f"User {user_id} added to group {group_id}")

    async with get_db_session() as session:
        # Check if membership already exists
        result = await session.execute(
            select(DirectoryGroupMembership).where(
                DirectoryGroupMembership.group_id == group_id,
                DirectoryGroupMembership.user_id == user_id
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            membership = DirectoryGroupMembership(
                id=str(uuid.uuid4()),
                group_id=group_id,
                user_id=user_id,
            )
            session.add(membership)
            await session.commit()


async def handle_group_user_removed(data: Dict[str, Any]):
    """Handle dsync.group.user_removed event."""
    directory_group = data.get("directory_group", data)
    directory_user = data.get("directory_user", {})

    group_id = directory_group.get("id")
    user_id = directory_user.get("id")

    logger.info(f"User {user_id} removed from group {group_id}")

    async with get_db_session() as session:
        result = await session.execute(
            select(DirectoryGroupMembership).where(
                DirectoryGroupMembership.group_id == group_id,
                DirectoryGroupMembership.user_id == user_id
            )
        )
        membership = result.scalar_one_or_none()

        if membership:
            await session.delete(membership)
            await session.commit()
