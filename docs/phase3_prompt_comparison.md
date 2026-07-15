# Phase 3 Deliverable: Prompt Comparison & Multi-Agent Routing Report

This report documents the design, prompt structure, and routing comparison for **Phase 3** of the ResolveDesk AI Multi-Agent System. It highlights the transition from the Phase 2 keyword-based baseline to the LLM-powered supervisor orchestration framework.

---

## 1. Supervisor Prompt Design

The **Supervisor Agent** acts as the central router and orchestrator of the customer support agent graph. It analyzes conversational history and routes to one of three specialist agents (`RAG Agent`, `SQL Agent`, or `Planner Agent`) or responds directly for general inquiries.

### System Prompt (`SUPERVISOR_SYSTEM_PROMPT`)
```text
You are the Supervisor Orchestrator for ResolveDesk AI Customer Support.
Your job is to read the customer conversation history and determine the next best step.

You have access to three specialist agent routing tools:
1. RouteToRAG: Call this if the customer asks for static company policies, guidelines, FAQs, instructions (such as changing passwords or editing settings), pricing packages, or troubleshooting help. You MUST use this tool for any informational questions about the product or its procedures, even if you think you know the answer.
2. RouteToSQL: Call this if the customer asks to check their specific account, database details, subscription info, tickets, or payment history.
3. RouteToPlanner: Call this for complex multi-step queries (e.g. Cancel account AND refund, or lookup a ticket AND search docs for details).

You should ONLY respond directly (without calling a tool) for simple greetings, pleasantries, or general chitchat (e.g., "hi", "hello", "thank you"). Do NOT attempt to answer questions about the product, settings, policies, or accounts directly; you must route them to the appropriate specialist agent.
```

> [!NOTE]
> **Prompt Reinforcement against Hallucinations**: In initial testing, LLM-based supervisors would occasionally answer product FAQs (like password resets) directly using their own pre-trained knowledge instead of calling the RAG tool. The prompt was reinforced to strictly forbid direct responses to product questions, ensuring all product queries retrieve grounded information from the database.

---

## 2. Prompt & Routing Comparison: Rule-Based vs. LLM Supervisor

The LLM-powered LangGraph router was evaluated against the Phase 2 baseline keyword router across several test cases:

| Scenario / Query | Phase 2 Keyword Router (Baseline) | Phase 3 LLM Tool-Calling Router (ChatOpenAI) | Comparison & Analysis |
| :--- | :--- | :--- | :--- |
| **Greeting / Chit-chat**<br>*"Hello there! How's it going?"* | **Response**: Greeting match or Fallback.<br>**Routing**: None. | **Response**: Direct chat greeting.<br>**Routing**: Direct Response (No tools invoked). | Both handle greetings cleanly, but the LLM provides natural, contextual conversation rather than hardcoded responses. |
| **Paraphrased Knowledge**<br>*"How do I get my money back?"* | **Response**: *"I'm sorry, I could not understand..."*<br>**Routing**: Failure (Requires exact keyword "refund"). | **Response**: Routes to RAG agent placeholder.<br>**Routing**: `RouteToRAG` (Invoked successfully). | **LLM Victory**: Semantically resolves "money back" to a refund query, routing it to the RAG specialist. |
| **Database lookup**<br>*"Show my subscription status"* | **Response**: Hardcoded DB error response.<br>**Routing**: Keyword matched subscription, but unable to query. | **Response**: Routes to SQL agent placeholder.<br>**Routing**: `RouteToSQL` (Invoked successfully). | **LLM Victory**: Detects database intent and routes to the SQL Agent node, carrying query variables in state. |
| **Complex Task**<br>*"I want to cancel my subscription and get my money back."* | **Response**: Hardcoded DB error response (hits "subscription" keyword first).<br>**Routing**: Keyword matched subscription, fails to capture multi-agent flow. | **Response**: Routes to Planner agent placeholder.<br>**Routing**: `RouteToPlanner` (Invoked successfully). | **LLM Victory**: Identifies that canceling (SQL) and refunding (RAG) is a complex task requiring the Planner to decompose the steps. |

---

## 3. LangGraph Routing Mechanism & State Trace

The Phase 3 graph is defined in `backend/app/agents/graph.py` using **LangGraph**. The workflow follows:

1. **State Initialization**: The client query is injected into the `AgentState` list of messages.
2. **Supervisor Execution**: The LLM parses state messages. If it decides to call a routing tool, the tool call is attached to the output `AIMessage`.
3. **Conditional Routing**: The `route_supervisor` edge checks the tool calls on the supervisor's output:
   * If a tool is called, the graph transitions to the matching specialist node (RAG, SQL, or Planner) to perform work and update the state.
   * If no tool is called (direct response), the graph routes directly to the Safety Agent.
4. **Safety Verification**: All worker nodes run through the `safety_node` (Safety Agent) for validation before the graph terminates (`END`).

---

## 4. Conclusion & Next Steps

Phase 3 establishes a robust orchestrator that solves the routing bottlenecks, lack of semantic understanding, and state management issues of Phase 2. 

The system has been integrated with  `ChatOpenAI`. Additionally, the RAG backend is connected to support a production-ready **Qdrant Server**.

With routing, state validation, and Qdrant Server integration complete, the system is fully prepared for Phase 4/5 integration, including building seed data generators and connecting specialists to live SQLite databases.
