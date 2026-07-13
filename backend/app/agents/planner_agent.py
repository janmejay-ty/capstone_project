# planner_agent.py
import os
import logging
from typing import Dict, Any
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from backend.app.agents.state import AgentState
from backend.app.tools.sql_tools import (
    customer_lookup,
    subscription_lookup,
    ticket_status,
    payment_history
)
from backend.app.tools.rag_tools import query_knowledge_base

logger = logging.getLogger(__name__)

@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the company documentation, guides, refund policies, FAQs, and API manuals for information matching the query.
    """
    chunks = query_knowledge_base(query, limit=3)
    if not chunks:
        return "No documentation found matching the search query."
    return "\n---\n".join(chunks)

PLANNER_SYSTEM_PROMPT = """You are the ResolveDesk AI Planner Specialist Agent.
Your job is to resolve complex, multi-step customer support requests (such as evaluations of cancellation and refund requests) by coordinating database lookups and documentation searches.

You have access to the following tools:
1. customer_lookup: Search for customer profiles (name, email, phone, ID).
2. subscription_lookup: Get subscription details and prices for a customer_id.
3. ticket_status: Get support ticket logs for a customer_id or specific ticket_id.
4. payment_history: Get payment records, invoice amounts, and statuses for a customer_id.
5. search_knowledge_base: Search the company documentation, guides, refund policies, FAQs, and API manuals.

Guidelines:
1. Before answering the user, you MUST formulate a clear step-by-step plan (e.g. "1. SQL: Lookup customer and subscription status. 2. RAG: Search company refund policy rules. 3. Analyze compliance.").
2. Execute the tools sequentially to fetch the required information.
3. If a customer ID or name is provided in the query context, you MUST run a data validation check:
   - Run customer_lookup to find the customer's profile using the ID (e.g. search for cust_013 or 013).
   - Compare the database name associated with that ID (e.g. Grace Lewis) with the customer name mentioned in the conversation (e.g. JJ).
   - If there is a name mismatch (i.e. the ID belongs to a different person than the one mentioned in the chat), you MUST explicitly warn the user about this profile mismatch and halt the process instead of offering plan upgrade/change instructions.
   - Run subscription_lookup to check their current active subscription. If they are already on the plan they want to change to (e.g. they want to upgrade to Pro but they are already on the Pro Plan), state this clearly and ask for clarification.
4. Once you gather the customer data and refund/cancellation guidelines, evaluate the request compliance:
   - Check the customer's subscription plan: monthly plans are strictly non-refundable. Annual plans are eligible for a 100% refund within 14 days of the initial transaction date.
   - Compare the start date of the subscription to the current date/transaction date to check the 14-day window.
   - Formulate a definitive conclusion on whether the user is eligible for cancellation and a refund.
5. Respond politely, detailing the facts of their subscription and the rules of the company policies, and summarize your final conclusion.
"""

def get_planner_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    
    if not api_key:
        logger.warning("OPENAI_API_KEY environment variable is missing. Planner LLM will fallback to mock responses.")
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

def planner_node(state: AgentState) -> Dict[str, Any]:
    # Find the last human query
    query = ""
    for msg in reversed(state["messages"]):
        if msg.type == "human":
            query = msg.content
            break

    if not query:
        return {
            "messages": [AIMessage(content="📋 Planner Agent: No query found.")],
            "current_agent": "Planner Agent"
        }

    # Dynamically define plan steps based on user query content
    q_lower = query.lower()
    if any(k in q_lower for k in ["refund", "cancel", "cancellation", "money"]):
        plan_steps = [
            "1. SQL: Lookup customer subscription info",
            "2. RAG: Query company refund policy rules",
            "3. Assess eligibility & output resolution"
        ]
    else:
        plan_steps = [
            "1. SQL: Search customer database records",
            "2. RAG: Search product guides and FAQs",
            "3. Synthesize customer resolution plan"
        ]

    llm = get_planner_llm()
    tools = [customer_lookup, subscription_lookup, ticket_status, payment_history, search_knowledge_base]

    if llm is None:
        # Fallback Mock Planner Response if API key is missing
        mock_text = (
            f"📋 [Planner Agent Fallback]\n"
            f"I see you asked: '{query}'. However, the OpenAI API key is missing. "
            f"Planner Agent requires an API key to orchestrate search tools."
        )
        return {
            "messages": [AIMessage(content=mock_text)],
            "current_agent": "Planner Agent",
            "plan_steps": plan_steps
        }

    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)

    # Build messages history, filtering out supervisor routing and tool execution messages from history.
    messages = []
    for msg in state["messages"]:
        if msg.type in ["human", "user"]:
            messages.append(msg)
        elif msg.type in ["ai", "assistant"] and not (hasattr(msg, "tool_calls") and msg.tool_calls):
            messages.append(msg)
        
    feedback = state.get("feedback_note", "")
    sys_prompt = PLANNER_SYSTEM_PROMPT
    if feedback:
        sys_prompt += f"\n\nAdaptive Tone Guideline:\n{feedback}"
    system_msg = SystemMessage(content=sys_prompt)

    sql_results = {}
    new_messages = []

    # Run up to 4 turns of tool executions
    for _ in range(4):
        response = llm_with_tools.invoke([system_msg] + messages)
        new_messages.append(response)
        messages.append(response)

        if not response.tool_calls:
            break

        # Handle tool calls
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_call_id = tc["id"]

            try:
                if tool_name == "customer_lookup":
                    out = customer_lookup.invoke(tool_args)
                    sql_results[tool_name] = {"args": tool_args, "data": out}
                elif tool_name == "subscription_lookup":
                    out = subscription_lookup.invoke(tool_args)
                    sql_results[tool_name] = {"args": tool_args, "data": out}
                elif tool_name == "ticket_status":
                    out = ticket_status.invoke(tool_args)
                    sql_results[tool_name] = {"args": tool_args, "data": out}
                elif tool_name == "payment_history":
                    out = payment_history.invoke(tool_args)
                    sql_results[tool_name] = {"args": tool_args, "data": out}
                elif tool_name == "search_knowledge_base":
                    out = search_knowledge_base.invoke(tool_args)
                else:
                    out = f"Error: Tool {tool_name} not found."
            except Exception as e:
                out = f"Error executing tool: {e}"

            tool_msg = ToolMessage(content=str(out), tool_call_id=tool_call_id)
            new_messages.append(tool_msg)
            messages.append(tool_msg)

    # Return updates to LangGraph state
    return {
        "messages": new_messages,
        "current_agent": "Planner Agent",
        "plan_steps": plan_steps,
        "sql_results": sql_results
    }
