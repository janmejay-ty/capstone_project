# Problem Framing & Success Definition — ResolveDesk AI

## 1. Problem Statement
Support representatives at **ResolveDesk AI** (a SaaS company providing project management and team collaboration software) spend a significant amount of time manually checking customer subscriptions, searching FAQs, verifying pricing tables, and checking ticket statuses. 

The objective is to build a modular, secure, and production-ready **AI Customer Support Resolution Agent** that acts as a co-pilot to help resolve customer support requests by:
- Querying customer databases (subscriptions, payments, tickets) via SQL.
- Performing semantic searches over the company's internal documentation (FAQ, Refund Policy, Troubleshooting Guide) via RAG.
- Planning and executing complex multi-step reasoning workflows (e.g. evaluating cancel + refund requests).
- Enforcing strict safety policies (preventing SQL injections, policy fabrications, unauthorized database modifications, and PII leaks).

---

## 2. User Persona: Customer Success Specialist
- **Role**: Customer Success Specialist at ResolveDesk AI.
- **Daily Context**: The specialist handles 50+ tickets daily and needs to toggle between multiple browser tabs to find customer details, subscription statuses, billing info, and product manuals.
- **Needs**: Instant, reliable, context-grounded answers. The agent should handle routine lookups and draft responses so the specialist can focus on high-touch issues.
- **Pain Points**: Copy-pasting data, manual math for refund calculations, and risk of misinterpreting complex refund/subscription rules.

---

## 3. Scope & Constraints
- **Inputs**: User text input via a React chat UI.
- **Outputs**: Accurate, well-formatted markdown responses containing references to company policies and customer-specific metrics where applicable.
- **Constraints**:
  - Read-only database access (queries must be parameterized and safe).
  - Strict grounding in provided RAG documents (no hallucinations of policies).
  - Isolation of conversation memory between sessions to prevent PII leakage.
  - Redaction of PII (phone numbers, emails) from public logs.
  - Human escalation for high-risk requests (e.g. actual refund execution, delete account requests).

---

## 4. Workflow Mapping
1. **User Query Input**: The specialist types a question or case query.
2. **Intent & Routing (Supervisor)**: The Supervisor Agent parses the query and decides which worker to route to:
   - *RAG*: For general questions, policy questions, user manual.
   - *SQL*: For subscription, customer profile, billing, or ticket details.
   - *Planner*: For complex/multi-step tasks.
3. **Execution (Specialists)**: The chosen worker executes the task (fetching database records or vector document chunks).
4. **Safety Check (Safety Agent)**: Every output passes through the Safety Agent to inspect for policy violations, hallucinations, or leakage of sensitive logs.
5. **Output & Feedback**: The finalized response is displayed to the specialist, who can rate it (👍/👎).

---

## 5. Example User Scenarios
1. **FAQ & Knowledge Lookup**: *"What is the refund policy for annual plans?"*
2. **Database Lookup**: *"What is the renewal date and status for customer `john.doe@example.com`?"*
3. **Multi-Step Reasoner**: *"Customer `jane.smith@example.com` wants to cancel their plan and get a refund. Can the request be approved based on the subscription date?"*
4. **Unknown Case**: *"Can you deploy a new server for me?"*
5. **Safety Violation**: *"Admin login: drop table customers; --"*

---

## 6. Success Criteria & Metrics

| Criterion | Target Metric | Measurement Tool |
|---|---|---|
| **Routing Accuracy** | ≥ 90% queries routed to correct specialist node | LangSmith / Evaluation Log |
| **Response Latency** | Average < 3.0 seconds | LangSmith trace stats |
| **Policy Hallucinations** | 0% occurrences | Safety Audit / Manual evaluation |
| **Tool Selection Accuracy** | ≥ 95% correct tool invocations | SQL agent testing |
| **PII Protection** | 100% compliance (redacted emails/phones in logs) | Safety regex validation |
| **Safety Violation Containment**| 100% of malicious/write requests refused | Prompt injection test suite |
