"""Authentication dependencies for FastAPI."""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from meeting_notes_agent.auth.security import decode_access_token, decode_refresh_token
from meeting_notes_agent.database import (
    Meeting,
    PlatformRole,
    Project,
    Task,
    TeamMembership,
    TeamRole,
    UserRepository,
    get_db,
)
from meeting_notes_agent.config.core.exceptions import AuthenticationError, AuthorizationError, to_http_exception


# Security scheme
security = HTTPBearer(auto_error=False)


async def enforce_active_team_resource_scope(
    request: Request,
    active_team_id: Annotated[UUID | None, Header(alias="X-Team-ID")] = None,
    db=Depends(get_db),
) -> None:
    """Keep ID-based resources inside the explicitly selected workspace.

    Membership authorization still runs in each service. This dependency adds
    the workspace-context boundary needed for users who legitimately belong to
    more than one Team, and deliberately conceals mismatched resource IDs.
    """
    if active_team_id is None:
        return

    resource_team_id = request.path_params.get("team_id") or request.query_params.get("team_id")
    project_id = request.path_params.get("project_id")
    meeting_id = request.path_params.get("meeting_id")
    task_id = request.path_params.get("task_id")
    if project_id:
        try:
            parsed_project_id = UUID(str(project_id))
        except ValueError:
            return
        project = db.query(Project).filter(Project.id == parsed_project_id).first()
        resource_team_id = project.team_id if project else None
    elif meeting_id:
        try:
            parsed_meeting_id = UUID(str(meeting_id))
        except ValueError:
            return
        meeting = db.query(Meeting).filter(Meeting.id == parsed_meeting_id).first()
        resource_team_id = meeting.team_id if meeting else None
    elif task_id:
        task = db.query(Task).filter(Task.id == task_id).first()
        resource_team_id = task.team_id if task else None

    if resource_team_id is not None:
        try:
            scoped_team_id = UUID(str(resource_team_id))
        except ValueError:
            return  # Let FastAPI's typed parameter validation return 422.
        if scoped_team_id != active_team_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> Optional["User"]:
    """Get current user if token is valid, otherwise return None."""
    if not credentials:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            return None
    except JWTError:
        return None

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        return None

    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> "User":
    """Get current authenticated user."""
    if not credentials:
        raise to_http_exception(AuthenticationError("Not authenticated"))

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            raise to_http_exception(AuthenticationError("Invalid token payload"))
    except JWTError as e:
        raise to_http_exception(AuthenticationError(str(e)))

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise to_http_exception(AuthenticationError("User not found"))
    if not user.is_active:
        raise to_http_exception(AuthenticationError("Account is disabled"))

    return user


async def get_current_active_user(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """Get current active user (alias for get_current_user)."""
    return current_user


async def get_current_admin(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """Get current user and verify admin role."""
    if current_user.platform_role != PlatformRole.PLATFORM_ADMIN:
        raise to_http_exception(AuthorizationError("Platform admin access required"))
    return current_user


def require_role(*allowed_roles: PlatformRole):
    """Dependency factory for role-based access control."""
    async def role_checker(current_user: "User" = Depends(get_current_user)) -> "User":
        if current_user.platform_role not in allowed_roles:
            raise to_http_exception(AuthorizationError(f"Requires one of: {', '.join(r.value for r in allowed_roles)}"))
        return current_user
    return role_checker


async def get_current_configuration_manager_id(
    current_user: "User" = Depends(get_current_user),
    active_team_id: Annotated[UUID | None, Header(alias="X-Team-ID")] = None,
    db=Depends(get_db),
) -> int:
    """Require authority to manage owner-scoped provider/workflow settings.

    Provider credentials remain attached to the authenticated account during the
    team migration. Platform operators and users who manage at least one team may
    access these controls; ordinary team members may not.
    """
    if current_user.platform_role == PlatformRole.PLATFORM_ADMIN:
        return current_user.id

    memberships = (
        db.query(TeamMembership)
        .filter(TeamMembership.user_id == current_user.id)
        .all()
    )
    if active_team_id is not None:
        membership = next(
            (item for item in memberships if item.team_id == active_team_id),
            None,
        )
    else:
        # Preserve compatibility for existing single-workspace clients. Once a
        # user belongs to multiple teams, the active scope must be explicit.
        membership = memberships[0] if len(memberships) == 1 else None

    if membership is None or membership.role not in {
        TeamRole.OWNER,
        TeamRole.ADMIN,
    }:
        raise to_http_exception(
            AuthorizationError(
                "Team owner or admin access is required for the active team"
            )
        )
    return current_user.id


async def get_current_user_from_refresh_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> "User":
    """Get current user from refresh token."""
    if not credentials:
        raise to_http_exception(AuthenticationError("Not authenticated"))

    try:
        payload = decode_refresh_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            raise to_http_exception(AuthenticationError("Invalid token payload"))
    except JWTError as e:
        raise to_http_exception(AuthenticationError(str(e)))

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise to_http_exception(AuthenticationError("User not found"))
    if not user.is_active:
        raise to_http_exception(AuthenticationError("Account is disabled"))

    return user


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> int:
    """Get an active user ID from a valid token and current database state."""
    if not credentials:
        raise to_http_exception(AuthenticationError("Not authenticated"))

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            raise to_http_exception(AuthenticationError("Invalid token payload"))
    except JWTError as e:
        raise to_http_exception(AuthenticationError(str(e)))

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise to_http_exception(AuthenticationError("User not found or disabled"))
    return user.id


def require_admin(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """Require admin role."""
    if current_user.platform_role != PlatformRole.PLATFORM_ADMIN:
        raise to_http_exception(AuthorizationError("Platform admin access required"))
    return current_user


require_platform_admin = require_admin


# Import User at the end to avoid circular imports
from meeting_notes_agent.database.models import User
