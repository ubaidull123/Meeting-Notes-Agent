"""One-time, explicit ownership migration for legacy meetings.

Usage:
    python -m meeting_notes_agent.database.assign_legacy_meeting_owner \
        --meeting-id <uuid> --owner-email <user@example.com>
"""
import argparse

from meeting_notes_agent.database.postgresdb import assign_legacy_meeting_owner


def main() -> None:
    parser = argparse.ArgumentParser(description="Assign an unowned legacy meeting to a user")
    parser.add_argument("--meeting-id", required=True)
    parser.add_argument("--owner-email", required=True)
    args = parser.parse_args()

    if not assign_legacy_meeting_owner(args.meeting_id, args.owner_email):
        raise SystemExit("No unowned meeting was updated; check the meeting ID and current ownership.")
    print("Legacy meeting ownership assigned.")


if __name__ == "__main__":
    main()
