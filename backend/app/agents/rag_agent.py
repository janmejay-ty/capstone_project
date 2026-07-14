import os
import logging
from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.app.agents.state import AgentState
from backend.app.tools.rag_tools import query_knowledge_base

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are the ResolveDesk AI RAG Specialist Agent.
Your job is to answer customer questions strictly based on the retrieved company documents below.

Retrieved Context Chunks:
{context}

Guidelines:
1. Be concise, polite, and direct in your response.
2. Do NOT fabricate any policies, features, or details that are not explicitly stated in the context above.
3. If the customer asks a general question about a policy or system feature (e.g., "What is privacy policy?"), interpret it as a request for ResolveDesk AI's specific policy or feature, and answer using the details from the retrieved context.
4. If the retrieved context does not contain enough information to answer the question, state: "I'm sorry, but I couldn't find information in the documentation to answer your request."
5. GUARDRAIL: Never ask the user whether to proceed, confirm, execute, send, or delete anything. You must never ask questions like "Would you like me to do that?", "Should I proceed?", "Would you like to proceed?", or offer/ask to execute actions on their behalf. This system is advisory only — state findings directly, then stop. Do not ask open-ended questions about next steps or suggest executing any commands on their behalf.
"""

def get_rag_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    
    if not api_key:
        logger.warning("OPENAI_API_KEY environment variable is missing. RAG LLM will fallback to mock responses.")
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

def rag_node(state: AgentState) -> Dict[str, Any]:
    # Find the last human query
    query = ""
    for msg in reversed(state["messages"]):
        if msg.type == "human":
            query = msg.content
            break

    if not query:
        return {
            "messages": [AIMessage(content="📚 RAG Agent: No query found.")],
            "current_agent": "RAG Agent"
        }

    # Query local Qdrant vector database
    chunks = query_knowledge_base(query, limit=6)
    context = "\n---\n".join(chunks)

    llm = get_rag_llm()
    if llm is None:
        # Fallback Mock RAG Response if API key is missing
        mock_text = (
            f"📚 [RAG Agent Fallback]\n"
            f"I see you asked: '{query}'. However, the OpenAI API key is missing. "
            f"Retrieved document count: {len(chunks)}."
        )
        return {
            "messages": [AIMessage(content=mock_text)],
            "current_agent": "RAG Agent",
            "rag_context": context
        }

    # Build messages history, filtering out supervisor routing and tool execution messages from history.
    messages = []
    for msg in state["messages"]:
        if msg.type in ["human", "user"]:
            messages.append(msg)
        elif msg.type in ["ai", "assistant"] and not (hasattr(msg, "tool_calls") and msg.tool_calls):
            messages.append(msg)

    feedback = state.get("feedback_note", "")
    sys_prompt = RAG_SYSTEM_PROMPT.format(context=context)
    if feedback:
        sys_prompt += f"\n\nAdaptive Tone Guideline:\n{feedback}"
    system_msg = SystemMessage(content=sys_prompt)

    response = llm.invoke([system_msg] + messages)

    return {
        "messages": [response],
        "current_agent": "RAG Agent",
        "rag_context": context
    }
