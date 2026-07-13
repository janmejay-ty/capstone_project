# sql_agent.py
import os
import logging
from typing import Dict, Any
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from backend.app.agents.state import AgentState
from backend.app.tools.sql_tools import (
    customer_lookup,
    subscription_lookup,
    ticket_status,
    payment_history,
    get_customer_count,
    get_all_customers
)

logger = logging.getLogger(__name__)

SQL_SYSTEM_PROMPT = """You are the ResolveDesk AI SQL Specialist Agent.
Your job is to look up customer records, subscriptions, payments, and ticket details from the live database.

You have access to the following read-only database search tools:
1. customer_lookup: Search for customer profiles (name, email, phone, ID).
2. subscription_lookup: Get subscription details and prices for a customer_id.
3. ticket_status: Get support ticket logs for a customer_id or specific ticket_id.
4. payment_history: Get payment records, invoice amounts, and statuses for a customer_id.
5. get_customer_count: Get the total number of customers registered in the database.
6. get_all_customers: Retrieve details (ID, name, email, phone number) for all registered customers.

Guidelines:
1. Use the search tools to retrieve database records before answering the user's question.
2. If you don't find enough information or customer_id is missing, use customer_lookup first to find the customer's ID from their email/name, and then query their subscriptions or payments.
3. If customer_lookup returns multiple customer records (e.g. duplicate names or multiple matches), list all matching customer choices with their name, email, and customer_id, and explicitly ask the user to clarify by providing the specific customer ID. Do not make assumptions or pick one yourself.
4. Respond concisely and politely, strictly based on the database results.
5. Do NOT make up database records or information that is not in the query results.
6. If the database returns no results, state clearly that you couldn't find the records.
"""

def get_sql_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    
    if not api_key:
        logger.warning("OPENAI_API_KEY environment variable is missing. SQL LLM will fallback to mock responses.")
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

def sql_node(state: AgentState) -> Dict[str, Any]:
    # Find the last human query
    query = ""
    for msg in reversed(state["messages"]):
        if msg.type == "human":
            query = msg.content
            break

    if not query:
        return {
            "messages": [AIMessage(content="🗄️ SQL Agent: No query found.")],
            "current_agent": "SQL Agent"
        }

    llm = get_sql_llm()
    tools = [customer_lookup, subscription_lookup, ticket_status, payment_history, get_customer_count, get_all_customers]

    if llm is None:
        # Fallback Mock SQL Response if API key is missing
        mock_text = (
            f"🗄️ [SQL Agent Fallback]\n"
            f"I see you asked: '{query}'. However, the OpenAI API key is missing. "
            f"Database lookups are not supported without an API key."
        )
        return {
            "messages": [AIMessage(content=mock_text)],
            "current_agent": "SQL Agent",
            "sql_results": {"error": "API key missing"}
        }

    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)

    # Build messages to invoke the chain, filtering out supervisor routing and tool execution messages from history.
    messages = []
    for msg in state["messages"]:
        if msg.type in ["human", "user"]:
            messages.append(msg)
        elif msg.type in ["ai", "assistant"] and not (hasattr(msg, "tool_calls") and msg.tool_calls):
            messages.append(msg)
        
    feedback = state.get("feedback_note", "")
    sys_prompt = SQL_SYSTEM_PROMPT
    if feedback:
        sys_prompt += f"\n\nAdaptive Tone Guideline:\n{feedback}"
    system_msg = SystemMessage(content=sys_prompt)

    sql_results = {}
    new_messages = []

    # Run a loop up to 3 turns to handle multi-step database lookups
    for _ in range(3):
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
                elif tool_name == "subscription_lookup":
                    out = subscription_lookup.invoke(tool_args)
                elif tool_name == "ticket_status":
                    out = ticket_status.invoke(tool_args)
                elif tool_name == "payment_history":
                    out = payment_history.invoke(tool_args)
                elif tool_name == "get_customer_count":
                    out = get_customer_count.invoke(tool_args)
                elif tool_name == "get_all_customers":
                    out = get_all_customers.invoke(tool_args)
                else:
                    out = f"Error: Tool {tool_name} not found."
            except Exception as e:
                out = f"Error executing tool: {e}"

            # Log for UI trace
            sql_results[tool_name] = {
                "args": tool_args,
                "data": out
            }

            tool_msg = ToolMessage(content=str(out), tool_call_id=tool_call_id)
            new_messages.append(tool_msg)
            messages.append(tool_msg)

    # Return updates to LangGraph state
    return {
        "messages": new_messages,
        "current_agent": "SQL Agent",
        "sql_results": sql_results
    }
