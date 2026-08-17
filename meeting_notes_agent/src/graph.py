from langgraph.graph import StateGraph, START, END
from meeting_notes_agent.src.Nodes.iv_summerize import summarize_meeting_notes
from src.state_schema import MeetingState
from src.Nodes.i_Input import get_input_node
from src.Nodes.ii_transcribe_audio import transcribe_audio
from src.Nodes.iii_clean_transcript import clean_transcript


def build_graph() -> StateGraph:
    """Build and return the meeting notes agent graph."""
    graph = StateGraph(MeetingState)

    graph.add_node("Input", get_input_node)
    graph.add_node("TranscribeAudio", transcribe_audio)
    graph.add_node("CleanTranscript", clean_transcript)
    graph.add_node("Summarize", summarize_meeting_notes)

    graph.add_edge(START, "Input")
    graph.add_edge("Input", "TranscribeAudio")
    graph.add_edge("TranscribeAudio", "CleanTranscript")
    graph.add_edge("CleanTranscript", "Summarize")
    graph.add_edge("Summarize", END)

    return graph


graph = build_graph()


if __name__ == "__main__":
    # Quick test compile
    app = graph.compile()
    print("Graph compiled successfully")
    print("Nodes:", list(app.get_graph().nodes.keys()))