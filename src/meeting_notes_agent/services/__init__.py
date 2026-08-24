"""Services package for Meeting Notes API."""
from meeting_notes_agent.services.auth_service import AuthService
from meeting_notes_agent.services.processing_service import ProcessingService
from meeting_notes_agent.services.task_service import TaskService
from meeting_notes_agent.services.product_settings_service import ProductSettingsService
from meeting_notes_agent.services.configuration_resolver import UserConfigurationResolver
from meeting_notes_agent.services.admin_service import AdminService
from meeting_notes_agent.services.ai_settings_service import AISettingsService
from meeting_notes_agent.services.credits_service import CreditsService
from meeting_notes_agent.services.email_settings_service import EmailSettingsService
from meeting_notes_agent.services.meeting_override_service import MeetingOverrideService

__all__ = [
    "AuthService",
    "ProcessingService",
    "TaskService",
    "ProductSettingsService",
    "UserConfigurationResolver",
    "AdminService",
    "AISettingsService",
    "CreditsService",
    "EmailSettingsService",
    "MeetingOverrideService",
]
