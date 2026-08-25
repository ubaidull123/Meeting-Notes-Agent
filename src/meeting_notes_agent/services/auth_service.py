"""Authentication service."""
from typing import Optional
from datetime import datetime, timedelta, timezone

from meeting_notes_agent.auth.security import (
    hash_password,
    verify_password,
    create_token_pair,
    decode_refresh_token,
)
from meeting_notes_agent.database import UserRepository, UserQuotaRepository, UserCreditsRepository, UserUsageRepository, get_db
from meeting_notes_agent.database.models import Team, TeamInvitation, TeamMembership, TeamRole, UserRole
from meeting_notes_agent.config.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ValidationError,
    NotFoundError,
)
from meeting_notes_agent.schemas.auth import UserRegister, UserLogin, ChangePasswordRequest
from meeting_notes_agent.schemas.user import UserProfileResponse, UserQuotaResponse, UserCreditsResponse, UserUsageResponse


class AuthService:
    """Authentication service for user management."""

    def __init__(self, db=None):
        self.db = db

    def _get_db(self):
        """Get database session."""
        if self.db:
            return self.db
        return next(get_db())

    @staticmethod
    def _accept_pending_invitations(db, user) -> int:
        invitations = (
            db.query(TeamInvitation)
            .filter(
                TeamInvitation.email == user.email.lower(),
                TeamInvitation.status == "pending",
            )
            .all()
        )
        accepted = 0
        for invitation in invitations:
            membership = (
                db.query(TeamMembership)
                .filter(
                    TeamMembership.team_id == invitation.team_id,
                    TeamMembership.user_id == user.id,
                )
                .first()
            )
            if membership is None:
                db.add(
                    TeamMembership(
                        team_id=invitation.team_id,
                        user_id=user.id,
                        role=invitation.role,
                        title=invitation.title,
                        department=invitation.department,
                    )
                )
            invitation.status = "accepted"
            invitation.accepted_by = user.id
            invitation.accepted_at = datetime.now(timezone.utc)
            accepted += 1
        return accepted

    def register(self, data: UserRegister) -> UserProfileResponse:
        """Register a new user."""
        db = self._get_db()
        user_repo = UserRepository(db)
        quota_repo = UserQuotaRepository(db)
        credits_repo = UserCreditsRepository(db)

        # Check if user already exists
        if user_repo.get_by_email(data.email):
            raise ConflictError("Email already registered")

        # Hash password
        password_hash = hash_password(data.password)

        # Create user
        user = user_repo.create(
            email=data.email,
            password_hash=password_hash,
            full_name=data.full_name,
            role=UserRole.USER,
        )

        accepted_invitations = self._accept_pending_invitations(db, user)
        if accepted_invitations == 0:
            # Preserve the former independent-user experience for people who
            # register without an invitation. Invited collaborators land in
            # the workspace they were invited to instead of receiving a
            # distracting extra personal workspace.
            default_team = Team(
                name=f"{data.full_name.strip()[:248]}'s Team",
                description="Default workspace",
                created_by=user.id,
            )
            db.add(default_team)
            db.flush()
            db.add(
                TeamMembership(
                    team_id=default_team.id,
                    user_id=user.id,
                    role=TeamRole.OWNER,
                )
            )

        # Create default quota and credits with initial balance
        quota_repo.get_or_create(user.id)
        credits = credits_repo.get_or_create(user.id)
        # Give initial credits (matching monthly_credits default)
        credits_repo.add_credits(credits, 500, "Initial credit grant")

        db.commit()
        db.refresh(user)

        return self._build_profile_response(user, db)

    def login(self, data: UserLogin) -> tuple[str, str]:
        """Authenticate user and return token pair."""
        db = self._get_db()
        user_repo = UserRepository(db)

        user = user_repo.get_by_email(data.email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        if self._accept_pending_invitations(db, user):
            db.commit()

        access_token, refresh_token = create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        return access_token, refresh_token

    def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Refresh access token using refresh token."""
        db = self._get_db()
        user_repo = UserRepository(db)

        try:
            payload = decode_refresh_token(refresh_token)
            user_id = payload.get("user_id")
            if not user_id:
                raise AuthenticationError("Invalid token payload")
        except Exception as e:
            raise AuthenticationError(f"Invalid refresh token: {str(e)}")

        user = user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or disabled")

        access_token, new_refresh_token = create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        return access_token, new_refresh_token

    def get_profile(self, user_id: int) -> UserProfileResponse:
        """Get user profile with quota, credits, and usage."""
        db = self._get_db()
        user_repo = UserRepository(db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        return self._build_profile_response(user, db)

    def update_profile(self, user_id: int, full_name: str) -> UserProfileResponse:
        """Update user profile."""
        db = self._get_db()
        user_repo = UserRepository(db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        user_repo.update(user, full_name=full_name)
        db.commit()
        db.refresh(user)

        return self._build_profile_response(user, db)

    def change_password(self, user_id: int, data: ChangePasswordRequest) -> None:
        """Change user password."""
        db = self._get_db()
        user_repo = UserRepository(db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        if not verify_password(data.current_password, user.password_hash):
            raise ValidationError("Current password is incorrect")

        new_password_hash = hash_password(data.new_password)
        user_repo.update_password(user, new_password_hash)
        db.commit()

    def deactivate_user(self, user_id: int) -> None:
        """Deactivate user (admin)."""
        db = self._get_db()
        user_repo = UserRepository(db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        user_repo.update(user, is_active=False)
        db.commit()

    def activate_user(self, user_id: int) -> None:
        """Activate user (admin)."""
        db = self._get_db()
        user_repo = UserRepository(db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        user_repo.update(user, is_active=True)
        db.commit()

    def _build_profile_response(self, user, db) -> UserProfileResponse:
        """Build user profile response with quota, credits, and usage."""
        quota_repo = UserQuotaRepository(db)
        credits_repo = UserCreditsRepository(db)
        usage_repo = UserUsageRepository(db)

        quota = quota_repo.get_by_user_id(user.id)
        credits = credits_repo.get_by_user_id(user.id)
        usage = usage_repo.get_by_user_id(user.id)

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            platform_role=user.platform_role,
            is_active=user.is_active,
            created_at=user.created_at,
            quota=UserQuotaResponse.model_validate(quota) if quota else None,
            credits=UserCreditsResponse.model_validate(credits) if credits else None,
            usage=[UserUsageResponse.model_validate(u) for u in usage] if usage else None,
        )
