import os
import sys
import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from langchain_core.messages import HumanMessage, AIMessage
from backend.app.agents.graph import graph


app = FastAPI(title="ResolveDesk AI API", version="1.0.0")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory history & feedback store for baseline agent
# As Phase 6/7 are implemented, this can be moved to SQLite / Session Checkpointers
chat_history_store: Dict[str, List[Dict[str, Any]]] = {}
feedback_store: List[Dict[str, Any]] = []

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    state: Dict[str, Any]

class FeedbackRequest(BaseModel):
    session_id: str
    message_index: int
    feedback_type: str  # "up" or "down"

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = request.session_id
    if session_id not in chat_history_store:
        chat_history_store[session_id] = []

    # Map previous memory history to LangChain message objects
    lang_messages = []
    for msg in chat_history_store[session_id]:
        if msg["role"] == "user":
            lang_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lang_messages.append(AIMessage(content=msg["content"]))

    # Append the new user message
    lang_messages.append(HumanMessage(content=request.message))

    # Invoke the LangGraph workflow
    try:
        inputs = {
            "messages": lang_messages,
            "current_agent": "Supervisor",
            "plan_steps": [],
            "rag_context": "",
            "sql_results": {},
            "safety_check": {"passed": True, "details": "Initial Check"},
            "session_id": session_id
        }
        config = {"configurable": {"thread_id": session_id}}
        result = graph.invoke(inputs, config)  # type: ignore
    except Exception as e:
        print(f"[ERROR] LangGraph execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent workflow execution error: {e}")

    # Extract final assistant response and trace variables
    final_response = "I am sorry, I am unable to generate a response."
    for msg in reversed(result["messages"]):
        if msg.type == "ai":
            if isinstance(msg.content, list):
                text_parts = []
                for part in msg.content:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif isinstance(part, str):
                        text_parts.append(part)
                final_response = "".join(text_parts)
            else:
                final_response = msg.content or ""
            break

    # Record user message in local chat store
    user_msg = {
        "role": "user", 
        "content": request.message, 
        "timestamp": datetime.datetime.now().isoformat()
    }
    chat_history_store[session_id].append(user_msg)

    # Record assistant message in local chat store with state trace
    state_trace = {
        "current_agent": result.get("current_agent", "Supervisor"),
        "plan_steps": result.get("plan_steps", []),
        "sql_results": result.get("sql_results", {}),
        "safety_check": result.get("safety_check", {"passed": True, "details": "No issues detected"})
    }
    
    agent_msg = {
        "role": "assistant",
        "content": final_response,
        "timestamp": datetime.datetime.now().isoformat(),
        "state": state_trace
    }
    chat_history_store[session_id].append(agent_msg)

    return ChatResponse(response=final_response, state=state_trace)

@app.post("/api/feedback")
async def feedback_endpoint(request: FeedbackRequest):
    feedback_store.append({
        "session_id": request.session_id,
        "message_index": request.message_index,
        "feedback_type": request.feedback_type,
        "timestamp": datetime.datetime.now().isoformat()
    })
    # Log feedback in terminal
    print(f"[FEEDBACK] Session {request.session_id}, msg index {request.message_index}: {request.feedback_type}")
    return {"status": "success", "message": "Feedback recorded"}

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    history = chat_history_store.get(session_id, [])
    return {"history": history}

@app.post("/api/clear/{session_id}")
async def clear_session(session_id: str):
    if session_id in chat_history_store:
        chat_history_store[session_id] = []
    return {"status": "success", "message": f"Session {session_id} cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
