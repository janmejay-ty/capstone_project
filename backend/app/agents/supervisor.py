import os
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from backend.app.agents.state import AgentState

logger = logging.getLogger(__name__)

class RouteToRAG(BaseModel):
    """Route the conversation to the RAG Agent to search for documentation, policies, refund terms, pricing plans, or FAQs."""
    reason: str = Field(description="Reason for routing to the RAG specialist.")

class RouteToSQL(BaseModel):
    """Route the conversation to the SQL Agent to lookup database records, customer subscriptions, ticket status, or payment history."""
    reason: str = Field(description="Reason for routing to the SQL specialist.")

class RouteToPlanner(BaseModel):
    """Route the conversation to the Planner Agent for complex, multi-step customer inquiries that require combining information or running multiple steps."""
    reason: str = Field(description="Reason for routing to the Planner.")

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Orchestrator for ResolveDesk AI Customer Support.
Your sole job is to read the customer conversation history and select the next specialist agent tool. You do not possess internal product or customer data, so you must always route.

You have access to three specialist agent routing tools:
1. RouteToRAG: Call for static product guides, FAQs, company policies (refund, privacy), pricing plans, or troubleshooting instructions (e.g., password reset, password changes). You MUST use this tool for any informational questions about the product.
2. RouteToSQL: Call to look up customer-specific live database records, subscriptions, invoice statuses, or ticket details.
3. RouteToPlanner: Call for complex multi-step queries requiring coordination of data lookups and policy checks (e.g., check database status and then find relevant guide).

Strict Guidelines:
- Only respond directly (no tool call) for simple greetings or pleasantries ("hi", "how are you", "thanks").
- Never answer product, billing, setup, or policy questions directly.
- Always review the entire conversation context to check if previous steps have already been resolved.

Examples:
- User: "Hello there!" -> Direct Response ("Hello! How can I help you today?")
- User: "How do I change my billing cycle?" -> RouteToRAG (General informational query)
- User: "Did my invoice #1024 go through?" -> RouteToSQL (Database record lookup)
- User: "I want to cancel my account and get a refund" -> RouteToPlanner (Complex cancel + refund workflow)
"""

def get_supervisor_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    
    if not api_key:
        logger.warning("OPENAI_API_KEY environment variable is missing. LLM features will fall back to dummy responses.")
        return None
    try:
        base_url_val = base_url if base_url else None
        return ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=api_key,
            base_url=base_url_val
        )
    except Exception as e:
        logger.error(f"Error initializing ChatOpenAI: {e}")
        return None

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    llm = get_supervisor_llm()
    
    if llm is None:
        # Fallback Mock Supervisor for local testing without API Key
        last_user_message = ""
        for msg in reversed(state["messages"]):
            if msg.type == "human":
                last_user_message = msg.content.lower()
                break
        
        # Simulated routing logic based on keywords
        if "refund" in last_user_message or "pricing" in last_user_message or "plan" in last_user_message:
            tool_calls = [{"name": "RouteToRAG", "args": {"reason": "Fallback: Refund or pricing keyword detected"}, "id": "call_mock_rag"}]
            response = AIMessage(content="Routing to RAG Agent...", tool_calls=tool_calls)
        elif any(kw in last_user_message for kw in ["subscription", "ticket", "payment", "customer", "invoice"]):
            tool_calls = [{"name": "RouteToSQL", "args": {"reason": "Fallback: Customer subscription or ticket keyword detected"}, "id": "call_mock_sql"}]
            response = AIMessage(content="Routing to SQL Agent...", tool_calls=tool_calls)
        elif "cancel" in last_user_message and "refund" in last_user_message:
            tool_calls = [{"name": "RouteToPlanner", "args": {"reason": "Fallback: Complex query cancel and refund detected"}, "id": "call_mock_planner"}]
            response = AIMessage(content="Routing to Planner Agent...", tool_calls=tool_calls)
        else:
            response = AIMessage(content="Hello! I am the ResolveDesk AI Supervisor. Please define your OPENAI_API_KEY in the .env file to enable full LLM operations.")
        
        return {
            "messages": [response],
            "current_agent": "Supervisor"
        }

    llm_with_tools = llm.bind_tools([RouteToRAG, RouteToSQL, RouteToPlanner])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SUPERVISOR_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm_with_tools
    response = chain.invoke({"messages": state["messages"]})
    
    return {
        "messages": [response],
        "current_agent": "Supervisor"
    }
