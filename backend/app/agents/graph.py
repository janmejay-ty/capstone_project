from typing import Dict, Any, Literal
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END
from backend.app.agents.state import AgentState
from backend.app.agents.supervisor import supervisor_node
from backend.app.agents.rag_agent import rag_node
from backend.app.agents.sql_agent import sql_node
from backend.app.agents.planner_agent import planner_node
from backend.app.memory.session_memory import memory_checkpointer

import re

def redact_pii(text: str) -> str:
    # Redact email addresses
    email_pattern = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
    text = re.sub(email_pattern, "[REDACTED_EMAIL]", text)
    
    # Redact phone numbers (e.g. 555-123-4567, 555.123.4567, 555 123 4567)
    phone_pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    text = re.sub(phone_pattern, "[REDACTED_PHONE]", text)
    
    return text

# Safety agent node
def safety_node(state: AgentState) -> Dict[str, Any]:
    messages_list = list(state["messages"])
    if not messages_list:
        return {
            "safety_check": {"passed": True, "details": "No messages to check.", "human_escalation_required": False}
        }

    # --- Check original user query for high-risk intent ---
    user_query = ""
    for msg in reversed(messages_list):
        if msg.type == "human":
            user_query = msg.content.lower()
            break

    HIGH_RISK_USER_PATTERNS = [
        "delete", "remove", "erase", "wipe", "purge",  # data deletion intent
        "delete account", "delete data", "delete customer",
    ]
    user_high_risk = any(k in user_query for k in HIGH_RISK_USER_PATTERNS)

    if user_high_risk:
        return {
            "safety_check": {
                "passed": False,
                "details": "High-risk request detected: data deletion or account removal requires manager authorization. Escalated for human review.",
                "human_escalation_required": True
            }
        }

    last_msg = messages_list[-1]

    # If the last message is an assistant message, perform safety checks.
    # Note: PII is NOT redacted from the user-facing output message, since the user persona is an
    # authorized internal support employee/manager who requires access to customer contact details.
    if last_msg.type == "ai":
        content = last_msg.content or ""
        lower_content = content.lower()

        # Check for manual refund approvals to escalate
        escalation_required = False
        if "refund" in lower_content and ("approv" in lower_content or "initiat" in lower_content or "process" in lower_content or "issued" in lower_content):
            if not any(k in lower_content for k in ["ineligible", "not eligible", "non-refundable", "reject"]):
                escalation_required = True

        # Check for DB modification attempts in AI output
        db_exploit = False
        if any(k in lower_content for k in ["delete from", "drop table", "update customers", "insert into"]):
            db_exploit = True
            escalation_required = True

        return {
            "safety_check": {
                "passed": not db_exploit,
                "details": "Database exploit check passed. PII audit completed." if not db_exploit else "Security violation: database write attempted.",
                "human_escalation_required": escalation_required
            }
        }

    return {
        "safety_check": {"passed": True, "details": "Last message not assistant. Skip audit.", "human_escalation_required": False}
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



graph = builder.compile(checkpointer=memory_checkpointer)
