from typing import Dict, Any, Literal
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END
from backend.app.agents.state import AgentState
from backend.app.agents.supervisor import supervisor_node
from backend.app.agents.rag_agent import rag_node

# Placeholder SQL agent node
def sql_node(state: AgentState) -> Dict[str, Any]:
    mock_msg = AIMessage(
        content=(
            "🗄️ [SQL Agent Placeholder]\n"
            "Querying database records... Live query capability will be added in Phase 5.\n"
            "SQL query statement: SELECT * FROM subscriptions WHERE customer_id = 'cust_123';"
        )
    )
    return {
        "messages": [mock_msg],
        "current_agent": "SQL Agent",
        "sql_results": {"query": "SELECT * FROM subscriptions WHERE customer_id = 'cust_123';", "status": "mock_success", "data": []}
    }

# Placeholder Planner agent node
def planner_node(state: AgentState) -> Dict[str, Any]:
    mock_msg = AIMessage(
        content=(
            "📋 [Planner Agent Placeholder]\n"
            "Decomposing task steps:\n"
            "1. Lookup customer transaction records via SQL Agent.\n"
            "2. Retrieve refund terms via RAG Agent.\n"
            "3. Validate refund policy compliance."
        )
    )
    return {
        "messages": [mock_msg],
        "current_agent": "Planner Agent",
        "plan_steps": ["1. SQL: Customer lookup", "2. RAG: Refund policy check", "3. Safety validation"]
    }

# Placeholder Safety agent node
def safety_node(state: AgentState) -> Dict[str, Any]:
    # Returns safety check updates to display in UI debug trace
    return {
        "safety_check": {
            "passed": True,
            "details": "PII clear. Compliance audit completed (Phase 3 Placeholder)."
        }
    }

# Conditional routing edge from supervisor
def route_supervisor(state: AgentState) -> Literal["rag", "sql", "planner", "safety"]:
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        tool_name = last_msg.tool_calls[0]["name"]
        if tool_name == "RouteToRAG":
            return "rag"
        elif tool_name == "RouteToSQL":
            return "sql"
        elif tool_name == "RouteToPlanner":
            return "planner"
    return "safety"

# Build Graph
builder = StateGraph(AgentState)  # type: ignore[arg-type]
builder.add_node("supervisor", supervisor_node)
builder.add_node("rag", rag_node)
builder.add_node("sql", sql_node)
builder.add_node("planner", planner_node)
builder.add_node("safety", safety_node)

builder.set_entry_point("supervisor")

# Conditional edges
builder.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {
        "rag": "rag",
        "sql": "sql",
        "planner": "planner",
        "safety": "safety"
    }
)

# Connect worker nodes to safety check
builder.add_edge("rag", "safety")
builder.add_edge("sql", "safety")
builder.add_edge("planner", "safety")
builder.add_edge("safety", END)

graph = builder.compile()
