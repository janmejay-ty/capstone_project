import os
import sys
import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from backend.app.agents.graph import graph
import sqlite3
import uvicorn

# Load env variables
load_dotenv()

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))




app = FastAPI(title="ResolveDesk AI API", version="1.0.0")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite DB Path
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database", "support.db"))

chat_history_store: Dict[str, List[Dict[str, Any]]] = {}

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

    # Check SQLite for any negative ratings (downvotes) in this session to trigger adaptive behaviour

    feedback_note = ""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM feedback_logs WHERE session_id = ? AND rating = 'down'",
            (session_id,)
        )
        downvotes = cursor.fetchone()[0]
        conn.close()
        if downvotes > 0:
            feedback_note = "SYSTEM NOTICE: The user previously downvoted responses in this session. Adjust your tone to be extra polite, clear, and detailed."
    except Exception as e:
        print(f"[FEEDBACK CHECK ERROR] {e}")

    # Invoke the LangGraph workflow with the new human message.
    # The checkpointer (MemorySaver) will automatically retrieve and append to session history.
    try:
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "current_agent": "Supervisor",
            "plan_steps": [],
            "rag_context": "",
            "sql_results": {},
            "safety_check": {"passed": True, "details": "Initial Check"},
            "session_id": session_id,
            "feedback_note": feedback_note
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
  
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback_logs (session_id, message_index, rating, created_at) VALUES (?, ?, ?, ?)",
            (request.session_id, request.message_index, request.feedback_type, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[FEEDBACK SAVE ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
        
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

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
