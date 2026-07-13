from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    State representing the context of a customer support interaction.
    """
    messages: Annotated[list, add_messages]
    current_agent: str
    plan_steps: List[str]
    rag_context: str
    sql_results: Dict[str, Any]
    safety_check: Dict[str, Any]
    session_id: str
    feedback_note: str
