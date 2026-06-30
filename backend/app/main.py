import os
import sys
import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.app.agents.baseline_agent import RuleBasedSupervisor
except ImportError:
    from backend.app.agents.supervisor import RuleBasedSupervisor

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

    # Record user message
    user_msg = {"role": "user", "content": request.message, "timestamp": datetime.datetime.now().isoformat()}
    chat_history_store[session_id].append(user_msg)

    # Initialize agent
    agent = RuleBasedSupervisor()
    
    # Run agent
    response_text = agent.handle_query(request.message)

    # Mock state updates for the baseline agent to show trace panel info
    # Later phases will return real LangGraph state variables
    current_agent = "Supervisor (Baseline)"
    plan_steps = []
    sql_results = {}
    safety_check = {"passed": True, "details": "No issues detected (Baseline)"}

    # Custom mock outputs for trace demonstration
    if "refund" in request.message.lower():
        current_agent = "RAG Agent"
        safety_check = {"passed": True, "details": "PII clear. Refund policy verified."}
    elif any(kw in request.message.lower() for kw in ["subscription", "ticket", "payment", "customer", "invoice"]):
        current_agent = "SQL Agent"
        sql_results = {"error": "Unable to retrieve live customer records or account data."}

    # Record agent message
    agent_msg = {
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.datetime.now().isoformat(),
        "state": {
            "current_agent": current_agent,
            "plan_steps": plan_steps,
            "sql_results": sql_results,
            "safety_check": safety_check
        }
    }
    chat_history_store[session_id].append(agent_msg)

    return ChatResponse(response=response_text, state=agent_msg["state"])

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
