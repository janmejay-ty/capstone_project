# Phase 7: Safety Agent & Adaptive Behaviour Report

This report documents the design, technical implementation, and verification results for **Phase 7** of the ResolveDesk AI Multi-Agent System. This phase focuses on post-processing response validation (PII auditing, DB write blocks, refund escalation flags), dynamic prompt adaptation based on SQLite feedback logs, and customer name-to-ID mismatch checks.

---

## 1. Safety Node Guardrails

We implemented the `safety_node` in [graph.py](file:///c:/Users/User/Desktop/python/capstone_project/backend/app/agents/graph.py) to audit all final AI responses before they are returned to the client:

* **PII Background Auditing**: Scans assistant messages for email addresses and phone numbers. To align with the **internal support employee/manager persona** (who needs to see contact details to resolve support issues), PII is NOT redacted in the user-facing text, but is logged as audited.
* **Database Write Block**: Scans outputs for SQL injection patterns or data modification keywords (e.g. `DELETE FROM`, `UPDATE customers`, `DROP TABLE`). If detected, the safety check is marked as failed (`passed = False`), and a security warning is raised.
* **Manual Refund Escalation**: Scans for phrases approving or processing a refund (e.g. `"refund approved"`, `"refund has been initiated"`). It sets `human_escalation_required = True` to flag the response for supervisor review.

---

## 2. SQLite Feedback Loops & Adaptive Prompts

We built a live feedback collection and prompt adaptation loop to adjust agent behaviors based on historical ratings:

### 2.1. SQLite Feedback Schema
We created the `feedback_logs` table in [schema.sql](file:///c:/Users/User/Desktop/python/capstone_project/database/schema.sql) to record user thumbs-up/thumbs-down ratings:
```sql
CREATE TABLE IF NOT EXISTS feedback_logs (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    message_index INTEGER NOT NULL,
    rating TEXT NOT NULL, -- 'up' or 'down'
    created_at TEXT NOT NULL
);
```

### 2.2. API Ingestion
* **[main.py](file:///c:/Users/User/Desktop/python/capstone_project/backend/app/main.py)**: Added the `/api/feedback` POST endpoint to write ratings to `feedback_logs`.
* **Runtime Ingestion**: When `/api/chat` is invoked, it queries the database for downvotes under that `session_id`. If downvotes are present, it injects a tone guide note into the graph state's `feedback_note`.

### 2.3. Agent Dynamic Tone Adaptation
* **[supervisor.py](file:///c:/Users/User/Desktop/python/capstone_project/backend/app/agents/supervisor.py)**, **[sql_agent.py](file:///c:/Users/User/Desktop/python/capstone_project/backend/app/agents/sql_agent.py)**, and **[planner_agent.py](file:///c:/Users/User/Desktop/python/capstone_project/backend/app/agents/planner_agent.py)**:
  * Read `state.get("feedback_note")` at runtime and append the tone warnings dynamically to their LLM system instructions, adjusting outputs to be extra detailed and polite.

---

## 3. Orchestration Prompt Updates: Plan Changes & Name Validation

To resolve plan change bypasses and ensure correct routing/validation, we introduced supervisor routing updates and planner validation rules:

### 3.1. Supervisor Routing Update
We updated `SUPERVISOR_SYSTEM_PROMPT` to route any customer-specific plan upgrades, downgrades, or cancellations containing customer details directly to `RouteToPlanner` (instead of routing directly to RAG).

### 3.2. Planner Customer Name-to-ID Mismatch Validation
We updated `PLANNER_SYSTEM_PROMPT` to enforce data integrity checks:
* When a customer ID or name is provided, the planner must run `customer_lookup` and compare the database name with the name mentioned.
* If a mismatch occurs (e.g. ID `013` belongs to Alice Taylor but name JJ was requested), it halts execution and issues a warning.
* It checks `subscription_lookup` to ensure a customer is not upgraded to their current plan tier.

### 3.3. Numeric ID Auto-Padding
* **[sql_tools.py](file:///c:/Users/User/Desktop/python/capstone_project/backend/app/tools/sql_tools.py)**: Refactored `customer_lookup` to auto-pad numeric IDs (e.g., matching `"013"` or `"13"` to `"cust_013"`).

---

## 4. Verification Logs

We validated the safety audits, feedback loops, and plan verification rules using automated test runs:

### 4.1. Safety Validation Output (`test_safety_agent.py`)
```
==================================================
TEST 1: Unit Test safety_node
==================================================
Original text: 'Sure, the customer's email is john.doe@example.com and his phone is +1-555-718-5333.'
Redacted text: 'Sure, the customer's email is [REDACTED_EMAIL] and his phone is +[REDACTED_PHONE].'
PII Redaction assertion passed!
Escalation check output: {'passed': True, 'details': 'Database exploit check passed. PII audit completed.', 'human_escalation_required': True}
Refund Escalation check assertion passed!
Exploit check output: {'passed': False, 'details': 'Security violation: database write attempted.', 'human_escalation_required': True}
Database Write Rejection check assertion passed!
```

### 4.2. Name-to-ID Mismatch Block Output (`test_planner_agent.py`)
* **Input Turn 1**: `"JJ wants to change plan."`
* **Input Turn 2**: `"He wants to upgrade the plan, his ID is 013"`
* **Planner Active Decision**:
```
Final active agent: Planner Agent
Plan tasks: ['1. SQL: Search customer database records', '2. RAG: Search product guides and FAQs', '3. Synthesize customer resolution plan']
Response:
It seems there is a profile mismatch. The customer ID "013" belongs to Alice Taylor, not JJ. Please verify the customer ID or provide the correct details for JJ so I can assist you further.
```
