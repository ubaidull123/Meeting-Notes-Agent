"""Verify durable human and email review checkpoints on PostgreSQL."""

from __future__ import annotations

import json
import os
from uuid import uuid4

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from meeting_notes_agent.state_schema import MeetingState


def human_review(state: MeetingState) -> dict:
    response = interrupt({"type": "human_review"})
    return {"human_review_decision": response["decision"]}


def email_review(state: MeetingState) -> dict:
    response = interrupt({"type": "email_review"})
    return {"email_review_decision": response["decision"]}


def compile_graph(connection):
    checkpointer = PostgresSaver(connection)
    checkpointer.setup()
    builder = StateGraph(MeetingState)
    builder.add_node("HumanReview", human_review)
    builder.add_node("EmailReview", email_review)
    builder.add_edge(START, "HumanReview")
    builder.add_edge("HumanReview", "EmailReview")
    builder.add_edge("EmailReview", END)
    return builder.compile(checkpointer=checkpointer)


def connect(database_url: str):
    return psycopg.connect(
        database_url,
        autocommit=True,
        prepare_threshold=0,
    )


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    thread_id = f"postgres-review-{uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}
    state = MeetingState(
        meeting_title="PostgreSQL checkpoint verification",
        transcript_text="A representative transcript.",
    )

    with connect(database_url) as first_connection:
        first_graph = compile_graph(first_connection)
        first_result = first_graph.invoke(state.model_dump(), config=config)
        assert first_result["__interrupt__"][0].value["type"] == "human_review"

    with connect(database_url) as second_connection:
        second_graph = compile_graph(second_connection)
        second_result = second_graph.invoke(
            Command(resume={"decision": "approve"}), config=config
        )
        assert second_result["human_review_decision"] == "approve"
        assert second_result["__interrupt__"][0].value["type"] == "email_review"

    with connect(database_url) as third_connection:
        third_graph = compile_graph(third_connection)
        final_result = third_graph.invoke(
            Command(resume={"decision": "approve"}), config=config
        )
        assert final_result["human_review_decision"] == "approve"
        assert final_result["email_review_decision"] == "approve"

    print(
        json.dumps(
            {
                "postgres_checkpoint_resume": "passed",
                "separate_connections": 3,
                "human_review_persisted": True,
                "email_review_persisted": True,
            }
        )
    )


if __name__ == "__main__":
    main()
