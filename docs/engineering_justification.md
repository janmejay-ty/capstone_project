# ResolveDesk AI: Engineering Justification Report

This document details the architectural decisions and system design justifications for the ResolveDesk AI Multi-Agent Support Co-Pilot system.

---

## 1. Multi-Agent Design vs. Monolithic LLM Prompts

Rather than relying on a single monolithic system prompt with dozens of tools, we chose a modular **Supervisor-Specialist Multi-Agent Architecture** compiled via LangGraph:

1. **Prompt Focus and Quality**: 
   - A single LLM with 15+ SQL and RAG tools is highly prone to **tool-selection confusion**, hallucinations, and context dilution.
   - By dividing the labor, each Specialist Agent (SQL Specialist, RAG Specialist, Planner Specialist) operates with a hyper-focused, minimal set of tools and a clear, descriptive prompt. This dramatically reduces reasoning errors.
2. **Context Window Efficiency**:
   - The Supervisor only coordinates routing.
   - The Specialists only receive context relevant to their domain (e.g. the SQL agent doesn't see RAG guidelines; the RAG agent doesn't see database schemas). This optimizes token consumption and speeds up inference.
3. **Independent Scalability**:
   - We can modify, optimize, or swap LLM models for specific workers independently (e.g., using a cheaper, faster model for SQL queries and a reasoning-heavy model for the Planner Agent).

---

## 2. Rationale for Key Abstractions

### 2.1. The Planner Specialist Agent
* **Purpose**: Coordinates multi-step operations (e.g., Cancellation + Refund evaluations).
* **Justification**: Cancellations require looking up customer data (SQL), checking payments (SQL), fetching refund rules (RAG), and running a compliance logic check. Wrapping this in a multi-turn tool calling loop inside the `planner_node` prevents tool execution noise from polluting the supervisor's main chat history, keeping the conversational thread clean.

### 2.2. Isolated Session Memory Saver
* **Purpose**: Conversation history isolation.
* **Justification**: Using LangGraph's `MemorySaver` checkpointer allows the backend API to dynamically load session checkpoints using the client-provided `session_id` (mapped to `thread_id`). This completely isolates Alice's support tickets from Bob's, eliminating any risk of history leakage.

### 2.3. SQLite Feedback Loop & Adaptive Prompts
* **Purpose**: Direct feedback logging and dynamic tone correction.
* **Justification**: Storing thumbs-up/thumbs-down ratings in a persistent SQLite table (`feedback_logs`) provides a clean audit trail. By querying this table before starting a chat session, the backend can inject adaptive tone rules into the specialists' prompts dynamically, allowing the co-pilot to recover gracefully and adjust its style if a user was previously dissatisfied.

### 2.4. Safety Validation node (Post-Processing Gatekeeper)
* **Purpose**: Security audit proxy.
* **Justification**: By separating validation from generation, the `safety_node` acts as a final gatekeeper. It audits PII in the background, checks for database exploit keywords, and flags manual refund approvals. This guarantees safety compliance without adding overhead to the specialists' reasoning prompts.

---

## 3. Database Security Guardrails

* **SELECT-Only SQL Wrapper**: The database query engine intercepts all commands at the function wrapper level in `sql_tools.py` and rejects any statement containing write keywords (e.g. `INSERT`, `UPDATE`, `DROP`, `DELETE`). This ensures read-only safety even if the LLM is manipulated.
* **Profile Mismatch Intercept**: The Planner Agent checks the name associated with a customer ID before analyzing plan details. This prevents unauthorized customer account changes.
