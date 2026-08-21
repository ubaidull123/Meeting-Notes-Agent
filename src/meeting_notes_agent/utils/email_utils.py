"""Email utility functions for reliable Mailgun or Resend delivery."""
import random
import resend
import time
from email.utils import parseaddr
from html import escape
from typing import List, Optional, Any, Dict
from urllib.parse import urlencode

import httpx

from meeting_notes_agent.core.config import Settings

MAX_SEND_ATTEMPTS = 3


class EmailDeliveryError(RuntimeError):
    """An email failure enriched with retry and provider context."""

    def __init__(self, message: str, attempts: int, retryable: bool):
        super().__init__(message)
        self.attempts = attempts
        self.retryable = retryable


class ProviderResponseError(RuntimeError):
    """A provider response that exposes its HTTP status for retry decisions."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


def _is_retryable_error(error: Exception) -> bool:
    """Retry only transient provider and network failures."""
    status_code = getattr(error, "status_code", getattr(error, "code", None))
    if isinstance(status_code, int):
        return status_code in {408, 409, 425, 429} or status_code >= 500
    message = str(error).lower()
    return any(marker in message for marker in ("timeout", "timed out", "connection", "temporar", "rate limit", "server error"))


def _configured_resend_sender(from_email: Optional[str]) -> tuple[str, Optional[str]]:
    """Load Resend credentials and sender at call time."""
    current_settings = Settings()
    if not current_settings.resend_api_key:
        raise EmailDeliveryError(
            "RESEND_API_KEY is not configured.",
            attempts=0,
            retryable=False,
        )

    sender = (from_email or current_settings.resend_from_email).strip()
    _, sender_address = parseaddr(sender)
    if not sender_address or "@" not in sender_address:
        raise EmailDeliveryError(
            "RESEND_FROM_EMAIL must contain a valid sender address.",
            attempts=0,
            retryable=False,
        )

    # The SDK stores the key globally, so refresh it immediately before every
    # request. This supports key rotation without restarting the API process.
    resend.api_key = current_settings.resend_api_key
    return sender, current_settings.resend_test_recipient


def _configured_mailgun_sender(from_email: Optional[str]) -> tuple[Settings, str]:
    """Load Mailgun configuration and construct a valid sender."""
    current_settings = Settings()
    if not current_settings.mailgun_api_key:
        raise EmailDeliveryError("MAILGUN_API_KEY is not configured.", attempts=0, retryable=False)
    if not current_settings.mailgun_domain:
        raise EmailDeliveryError("MAILGUN_DOMAIN is not configured.", attempts=0, retryable=False)

    sender = (
        from_email
        or current_settings.mailgun_from_email
        or f"Meeting Notes <postmaster@{current_settings.mailgun_domain}>"
    ).strip()
    _, sender_address = parseaddr(sender)
    if not sender_address or "@" not in sender_address:
        raise EmailDeliveryError("MAILGUN_FROM_EMAIL must contain a valid sender address.", attempts=0, retryable=False)
    return current_settings, sender


def _validate_test_domain_recipients(
    sender: str,
    recipients: List[str],
    test_recipient: Optional[str],
) -> None:
    """Prevent known-invalid attendee sends from Resend's onboarding domain."""
    _, sender_address = parseaddr(sender)
    sender_domain = sender_address.rsplit("@", 1)[-1].lower()
    if sender_domain != "resend.dev":
        return

    test_recipient = (test_recipient or "").strip().lower()
    invalid_recipients = [
        address
        for address in recipients
        if not address.lower().endswith("@resend.dev")
        and (not test_recipient or address.lower() != test_recipient)
    ]
    if invalid_recipients:
        raise EmailDeliveryError(
            "RESEND_FROM_EMAIL uses the testing-only resend.dev domain. "
            "Set RESEND_TEST_RECIPIENT to the Resend account owner's email for local testing, "
            "or verify a domain and update RESEND_FROM_EMAIL before emailing attendees.",
            attempts=0,
            retryable=False,
        )


def _send_via_mailgun(
    settings: Settings,
    sender: str,
    to: List[str],
    subject: str,
    html: str,
    cc: Optional[List[str]],
    bcc: Optional[List[str]],
    text: Optional[str],
) -> Dict[str, Any]:
    """Send one Mailgun API request using HTTP Basic authentication."""
    fields: List[tuple[str, str]] = [
        ("from", sender),
        *(("to", address) for address in to),
        ("subject", subject),
        ("html", html),
    ]
    fields.extend(("cc", address) for address in cc or [])
    fields.extend(("bcc", address) for address in bcc or [])
    if text:
        fields.append(("text", text))

    endpoint = f"{settings.mailgun_base_url.rstrip('/')}/v3/{settings.mailgun_domain}/messages"
    response = httpx.post(
        endpoint,
        auth=("api", settings.mailgun_api_key or ""),
        # httpx does not consistently encode a sequence of repeated form keys
        # on every supported version. Encode it explicitly so each recipient is
        # sent as a separate `to` field, as expected by Mailgun.
        content=urlencode(fields).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    if response.status_code >= 400:
        try:
            detail = response.json().get("message") or response.text
        except ValueError:
            detail = response.text
        hint = ""
        if settings.mailgun_domain.startswith("sandbox") and response.status_code == 400:
            hint = " Mailgun sandbox domains can only send to authorized, verified recipients."
        raise ProviderResponseError(
            f"Mailgun rejected the email ({response.status_code}): {detail}.{hint}",
            response.status_code,
        )
    try:
        return response.json()
    except ValueError:
        return {"status_code": response.status_code, "message": response.text}


def send_email(
    to: List[str],
    subject: str,
    html: str,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    text: Optional[str] = None,
) -> Any:
    """
    Send an email using the configured provider (Mailgun or Resend).

    Args:
        to: List of recipient email addresses.
        subject: Email subject line.
        html: HTML content of the email.
        from_email: Optional sender override. Defaults to the selected provider's sender.
        cc: Optional list of CC recipients.
        bcc: Optional list of BCC recipients.
        text: Optional plain text version.

    Returns:
        dict: Response from the selected email provider.

    Raises:
        EmailDeliveryError: If configuration is invalid or delivery fails.
    """
    current_settings = Settings()
    provider = current_settings.email_provider.strip().lower()
    if provider not in {"mailgun", "resend"}:
        raise EmailDeliveryError(
            "EMAIL_PROVIDER must be either 'mailgun' or 'resend'.",
            attempts=0,
            retryable=False,
        )

    if provider == "mailgun":
        settings, sender = _configured_mailgun_sender(from_email)
    else:
        sender, test_recipient = _configured_resend_sender(from_email)
        all_recipients = [*to, *(cc or []), *(bcc or [])]
        _validate_test_domain_recipients(sender, all_recipients, test_recipient)

    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_SEND_ATTEMPTS + 1):
        try:
            if provider == "mailgun":
                response = _send_via_mailgun(settings, sender, to, subject, html, cc, bcc, text)
            else:
                params: resend.Emails.SendParams = {
                    "from": sender,
                    "to": to,
                    "subject": subject,
                    "html": html,
                }
                if cc:
                    params["cc"] = cc
                if bcc:
                    params["bcc"] = bcc
                if text:
                    params["text"] = text
                response = resend.Emails.send(params)
            return {"provider": provider, "attempts": attempt, "response": response}
        except Exception as exc:
            last_error = exc
            retryable = _is_retryable_error(exc)
            if not retryable or attempt == MAX_SEND_ATTEMPTS:
                raise EmailDeliveryError(str(exc), attempts=attempt, retryable=retryable) from exc
            # Exponential backoff plus a small jitter prevents retry bursts.
            time.sleep((2 ** (attempt - 1)) + random.uniform(0, 0.25))

    raise EmailDeliveryError(str(last_error or "Email delivery failed"), attempts=MAX_SEND_ATTEMPTS, retryable=False)


def send_meeting_summary_email(
    to: List[str],
    meeting_title: str,
    summary: str,
    decisions: List[str],
    action_items: List[str],
    from_email: Optional[str] = None,
) -> Any:
    """
    Send a formatted meeting summary email.

    Args:
        to: List of recipient email addresses.
        meeting_title: Title of the meeting.
        summary: Meeting summary text.
        decisions: List of decisions made.
        action_items: List of action items.
        from_email: Sender email address.

    Returns:
        dict: Response from the configured provider.
    """
    # Build HTML email content
    html_parts = [
        f"<h2>Meeting Summary: {escape(meeting_title)}</h2>",
        f"<p><strong>Summary:</strong></p>",
        f"<p>{escape(summary).replace(chr(10), '<br>')}</p>",
    ]

    if decisions:
        html_parts.append("<h3>Decisions Made</h3>")
        html_parts.append("<ul>")
        html_parts.extend(f"<li>{escape(d)}</li>" for d in decisions)
        html_parts.append("</ul>")

    if action_items:
        html_parts.append("<h3>Action Items</h3>")
        html_parts.append("<ul>")
        html_parts.extend(f"<li>{escape(a)}</li>" for a in action_items)
        html_parts.append("</ul>")

    html_content = "\n".join(html_parts)

    subject = f"Meeting Summary: {meeting_title}"

    return send_email(
        to=to,
        subject=subject,
        html=html_content,
        from_email=from_email,
    )
