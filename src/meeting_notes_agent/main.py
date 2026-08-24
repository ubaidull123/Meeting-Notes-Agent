#!/usr/bin/env python3
"""
Main entry point for the Meeting Notes Agent.

Usage:
    python -m meeting_notes_agent.main --transcript-text "..." --attendees "Name:email,Name:email" [--meeting-title "..."]
    python -m meeting_notes_agent.main --audio-file "path/to/audio.mp3" --attendees "Name:email,Name:email"
    python -m meeting_notes_agent.main --input-file "input.json"
    python -m meeting_notes_agent.main --interactive
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from meeting_notes_agent.graph import build_graph
from meeting_notes_agent.state_schema import MeetingState, Attendee


def parse_attendees(attendees_str: str) -> list[Attendee]:
    """Parse attendees from 'Name:email,Name:email' format."""
    attendees = []
    for pair in attendees_str.split(","):
        pair = pair.strip()
        if ":" not in pair:
            raise ValueError(f"Invalid attendee format: '{pair}'. Use 'Name:email'")
        name, email = pair.split(":", 1)
        attendees.append(Attendee(name=name.strip(), email=email.strip()))
    return attendees


def load_input_from_file(file_path: str) -> dict:
    """Load input data from a JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def run_interactive() -> MeetingState:
    """Run in interactive mode, prompting for input."""
    print("=== Meeting Notes Agent - Interactive Mode ===\n")

    meeting_title = input("Meeting title: ").strip() or "Untitled Meeting"

    date_str = input(f"Meeting date (YYYY-MM-DD) [{date.today()}]: ").strip()
    meeting_date = date.fromisoformat(date_str) if date_str else date.today()

    meeting_time = input("Meeting time (optional): ").strip() or None
    project_name = input("Project name (optional): ").strip() or None

    print("\nAttendees (enter 'Name:email' pairs, empty line to finish):")
    attendees = []
    while True:
        line = input("  ").strip()
        if not line:
            break
        if ":" not in line:
            print("  Format: Name:email")
            continue
        name, email = line.split(":", 1)
        attendees.append(Attendee(name=name.strip(), email=email.strip()))

    if not attendees:
        raise ValueError("At least one attendee is required")

    print("\nInput source (choose one):")
    print("  1. Transcript text")
    print("  2. Transcript file path")
    print("  3. Audio file path")
    choice = input("Choice [1]: ").strip() or "1"

    transcript_text = None
    transcript_file_path = None
    audio_file_path = None

    if choice == "1":
        print("\nPaste transcript text (Ctrl+D / Ctrl+Z to finish):")
        transcript_text = sys.stdin.read().strip()
        if not transcript_text:
            raise ValueError("Transcript text cannot be empty")
    elif choice == "2":
        transcript_file_path = input("Transcript file path: ").strip()
        if not transcript_file_path:
            raise ValueError("Transcript file path cannot be empty")
        if not Path(transcript_file_path).exists():
            raise FileNotFoundError(f"File not found: {transcript_file_path}")
    elif choice == "3":
        audio_file_path = input("Audio file path: ").strip()
        if not audio_file_path:
            raise ValueError("Audio file path cannot be empty")
        if not Path(audio_file_path).exists():
            raise FileNotFoundError(f"File not found: {audio_file_path}")
    else:
        raise ValueError("Invalid choice")

    agenda = []
    print("\nAgenda items (empty line to finish):")
    while True:
        item = input("  ").strip()
        if not item:
            break
        agenda.append(item)

    notes = input("\nAdditional notes (optional): ").strip() or None

    return MeetingState(
        meeting_title=meeting_title,
        meeting_date=meeting_date,
        meeting_time=meeting_time,
        project_name=project_name,
        transcript_text=transcript_text,
        transcript_file_path=transcript_file_path,
        audio_file_path=audio_file_path,
        attendees=attendees,
        agenda=agenda,
        notes=notes,
    )


def create_state_from_args(args: argparse.Namespace) -> MeetingState:
    """Create MeetingState from command line arguments."""
    attendees = parse_attendees(args.attendees)

    # Load from file if provided
    if args.input_file:
        data = load_input_from_file(args.input_file)
        return MeetingState(**data)

    # Build from individual args
    return MeetingState(
        meeting_title=args.meeting_title or "Untitled Meeting",
        meeting_date=date.fromisoformat(args.meeting_date) if args.meeting_date else date.today(),
        meeting_time=args.meeting_time,
        project_name=args.project_name,
        transcript_text=args.transcript_text,
        transcript_file_path=args.transcript_file,
        audio_file_path=args.audio_file,
        attendees=attendees,
        agenda=args.agenda.split(",") if args.agenda else [],
        notes=args.notes,
    )


def print_results(state: dict):
    """Print the results in a readable format."""
    print("\n" + "=" * 60)
    print("MEETING PROCESSING RESULTS")
    print("=" * 60)

    print(f"\nMeeting: {state.get('meeting_title', 'N/A')}")
    print(f"Date: {state.get('meeting_date', 'N/A')}")
    print(f"Meeting ID: {state.get('meeting_id', 'N/A')}")

    if state.get("summary"):
        print(f"\n--- SUMMARY ---")
        print(state["summary"])

    if state.get("decisions"):
        print(f"\n--- DECISIONS ---")
        for i, d in enumerate(state["decisions"], 1):
            print(f"  {i}. {d}")

    if state.get("action_items"):
        print(f"\n--- ACTION ITEMS ---")
        for i, a in enumerate(state["action_items"], 1):
            print(f"  {i}. {a}")

    if state.get("redacted_summary"):
        print(f"\n--- REDACTED SUMMARY ---")
        print(state["redacted_summary"])

    if state.get("redacted_decisions"):
        print(f"\n--- REDACTED DECISIONS ---")
        for i, d in enumerate(state["redacted_decisions"], 1):
            print(f"  {i}. {d}")

    if state.get("redacted_action_items"):
        print(f"\n--- REDACTED ACTION ITEMS ---")
        for i, a in enumerate(state["redacted_action_items"], 1):
            print(f"  {i}. {a}")

    if state.get("email_draft"):
        print(f"\n--- EMAIL DRAFT ---")
        print(state["email_draft"])

    if state.get("pm_tasks"):
        print(f"\n--- PM TASKS ---")
        for task in state["pm_tasks"]:
            print(f"  - {task.title} (Priority: {task.priority}, Status: {task.status})")

    if state.get("email_sent"):
        print(f"\n--- EMAIL SENT ---")
        print(f"Response: {state.get('email_response', 'N/A')}")

    if state.get("stored"):
        print(f"\n--- STORED IN DATABASE ---")
    elif state.get("storage_error"):
        print(f"\n--- STORAGE ERROR ---")
        print(state["storage_error"])

    print(f"\nTokens used: {state.get('tokens_used_accrued', 0)}")


def main():
    parser = argparse.ArgumentParser(
        description="Meeting Notes Agent - Process meeting transcripts/audio into structured notes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Input methods (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument("--transcript-text", help="Raw transcript text")
    input_group.add_argument("--transcript-file", help="Path to transcript file")
    input_group.add_argument("--audio-file", help="Path to audio file (MP3, WAV, M4A)")
    input_group.add_argument("--input-file", help="Path to JSON input file")
    input_group.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")

    # Common arguments
    parser.add_argument("--attendees", help="Attendees as 'Name:email,Name:email'")
    parser.add_argument("--meeting-title", help="Meeting title")
    parser.add_argument("--meeting-date", help="Meeting date (YYYY-MM-DD)")
    parser.add_argument("--meeting-time", help="Meeting time")
    parser.add_argument("--project-name", help="Project name")
    parser.add_argument("--agenda", help="Comma-separated agenda items")
    parser.add_argument("--notes", help="Additional notes")

    # Output options
    parser.add_argument("--output-json", help="Save full state to JSON file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only print summary")

    args = parser.parse_args()

    # Handle interactive mode
    if args.interactive:
        try:
            state = run_interactive()
        except (ValueError, FileNotFoundError, EOFError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Validate required args for non-interactive mode
        if not any([args.transcript_text, args.transcript_file, args.audio_file, args.input_file]):
            parser.error("One of --transcript-text, --transcript-file, --audio-file, --input-file, or --interactive is required")

        if not args.attendees and not args.input_file:
            parser.error("--attendees is required (unless using --input-file)")

        try:
            state = create_state_from_args(args)
        except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Build and run the graph
    print("Building graph...")
    graph = build_graph()

    # Generate a thread_id for the checkpointer
    import uuid
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("Processing meeting...")
    try:
        result = graph.invoke(state.model_dump(), config=config)
    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        sys.exit(1)

    # Output results
    if args.output_json:
        with open(args.output_json, "w") as f:
            # Convert non-serializable objects
            def default_serializer(obj):
                if hasattr(obj, "model_dump"):
                    return obj.model_dump()
                if hasattr(obj, "__dict__"):
                    return obj.__dict__
                return str(obj)
            json.dump(result, f, indent=2, default=default_serializer)
        print(f"Full state saved to {args.output_json}")

    if not args.quiet:
        print_results(result)
    else:
        # Just print key results
        if result.get("summary"):
            print(result["summary"])
        if result.get("action_items"):
            print("\nAction Items:")
            for a in result["action_items"]:
                print(f"  - {a}")


if __name__ == "__main__":
    main()