import os
import sys
import json
import time
from datetime import datetime

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from langchain_core.messages import HumanMessage
from backend.app.agents.graph import graph

def run_evaluation():
    cases_file = os.path.join(os.path.dirname(__file__), "eval_cases.json")
    if not os.path.exists(cases_file):
        print(f"Error: Scenarios file not found: {cases_file}")
        return
        
    with open(cases_file, "r") as f:
        cases = json.load(f)
        
    print("\n==================================================================================")
    print("                      ResolveDesk AI Automated Evaluation Suite                  ")
    print("==================================================================================")
    print(f"Total test cases to execute: {len(cases)}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("----------------------------------------------------------------------------------\n")
    
    results = []
    total_latency = 0.0
    routing_correct = 0
    safety_correct = 0
    groundedness_correct = 0
    
    for idx, case in enumerate(cases):
        case_id = case["id"]
        category = case["category"]
        query = case["query"]
        expected_agent = case["expected_agent"]
        expected_keywords = case["expected_keywords"]
        expected_safety = case["expected_safety_passed"]
        
        print(f"Running Case [{idx+1}/{len(cases)}] - ID: {case_id} ({category})")
        print(f"  Query: '{query}'")
        
        # Invoke Graph
        session_id = f"eval_session_{case_id}_{int(time.time())}"
        inputs = {
            "messages": [HumanMessage(content=query)],
            "current_agent": "Supervisor",
            "plan_steps": [],
            "rag_context": "",
            "sql_results": {},
            "safety_check": {"passed": True, "details": "Initial Check"},
            "session_id": session_id,
            "feedback_note": ""
        }
        config = {"configurable": {"thread_id": session_id}}
        
        start_time = time.time()
        try:
            res = graph.invoke(inputs, config)
            elapsed = time.time() - start_time
            total_latency += elapsed
            
            # Extract final response
            response = ""
            for msg in reversed(res["messages"]):
                if msg.type == "ai":
                    response = msg.content or ""
                    break
            
            # 1. Routing Metric
            actual_agent = res.get("current_agent", "Supervisor")
            # If safety check fails, routing is SQL or safety; let's treat actual agent as routed agent
            route_ok = actual_agent.lower().replace(" ", "") == expected_agent.lower().replace(" ", "")
            if route_ok:
                routing_correct += 1
                
            # 2. Safety Metric
            safety_check = res.get("safety_check", {"passed": True})
            safety_passed = safety_check.get("passed", True)
            safety_ok = safety_passed == expected_safety
            if safety_ok:
                safety_correct += 1
                
            # 3. Groundedness (Keyword Check)
            lower_response = response.lower()
            matched_keywords = [kw for kw in expected_keywords if kw.lower() in lower_response]
            grounded_ok = len(matched_keywords) == len(expected_keywords)
            if grounded_ok:
                groundedness_correct += 1
                
            print(f"  Elapsed: {elapsed:.2f}s | Route: {actual_agent} ({'OK' if route_ok else 'FAIL: Expected ' + expected_agent})")
            print(f"  Safety: Passed={safety_passed} ({'OK' if safety_ok else 'FAIL'})")
            print(f"  Keywords Matched: {len(matched_keywords)}/{len(expected_keywords)} ({'OK' if grounded_ok else 'FAIL'})")
            print("  ------------------------------------------------------------------------------")
            
            results.append({
                "id": case_id,
                "category": category,
                "latency": elapsed,
                "routing_ok": route_ok,
                "safety_ok": safety_ok,
                "grounded_ok": grounded_ok,
                "response": response
            })
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  [ERROR] Workflow failed: {e}")
            results.append({
                "id": case_id,
                "category": category,
                "latency": elapsed,
                "routing_ok": False,
                "safety_ok": False,
                "grounded_ok": False,
                "error": str(e)
            })
            
    # Calculate Overall Stats
    count = len(cases)
    avg_latency = total_latency / count if count > 0 else 0
    routing_acc = (routing_correct / count) * 100 if count > 0 else 0
    safety_acc = (safety_correct / count) * 100 if count > 0 else 0
    groundedness_acc = (groundedness_correct / count) * 100 if count > 0 else 0
    
    print("\n==================================================================================")
    print("                               EVALUATION DASHBOARD                              ")
    print("==================================================================================")
    print(f" Total Cases Executed  : {count}")
    print(f" Average Latency       : {avg_latency:.2f} seconds")
    print(f" Routing Accuracy      : {routing_acc:.1f}% ({routing_correct}/{count})")
    print(f" Safety Compliance     : {safety_acc:.1f}% ({safety_correct}/{count})")
    print(f" Content Groundedness   : {groundedness_acc:.1f}% ({groundedness_correct}/{count})")
    print("==================================================================================\n")
    
    # Save results summary to JSON for reporting
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": count,
        "average_latency": avg_latency,
        "routing_accuracy": routing_acc,
        "safety_compliance": safety_acc,
        "content_groundedness": groundedness_acc,
        "results": results
    }
    
    summary_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved evaluation metrics to: {summary_path}\n")

if __name__ == "__main__":
    run_evaluation()
