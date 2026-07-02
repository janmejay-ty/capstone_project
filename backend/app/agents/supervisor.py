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
Your job is to read the customer conversation history and determine the next best step.

You have access to three specialist agent routing tools:
1. RouteToRAG: Call this if the customer asks for static company policies, guidelines, FAQs, instructions (such as changing passwords or editing settings), pricing packages, or troubleshooting help. You MUST use this tool for any informational questions about the product or its procedures, even if you think you know the answer.
2. RouteToSQL: Call this if the customer asks to check their specific account, database details, subscription info, tickets, or payment history.
3. RouteToPlanner: Call this for complex multi-step queries (e.g. Cancel account AND refund, or lookup a ticket AND search docs for details).

You should ONLY respond directly (without calling a tool) for simple greetings, pleasantries, or general chitchat (e.g., "hi", "hello", "thank you"). Do NOT attempt to answer questions about the product, settings, policies, or accounts directly; you must route them to the appropriate specialist agent.
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
