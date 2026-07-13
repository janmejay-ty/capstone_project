# Phase 2: Baseline Rule-Based Agent Results

To prove that a simple rule-based system is insufficient for an industry-grade support application, I implemented a baseline Python agent using case-insensitive keyword matching (`backend/app/agents/baseline_agent.py`). 

I ran three specific test queries to demonstrate the major failure modes of this baseline system.

---

## Execution Log & Failures

### Execution 1: Semantic Paraphrasing Failure
* **User Query**: `"How do I get my money back?"`
* **Expected Result**: System identifies this as a refund policy query and provides the refund guidelines.
* **Actual Output**: 
  ```text
  RECEIVED QUERY: 'How do I get my money back?'
  RESPONSE: 'I'm sorry, I could not understand your request. '
  ```
* **Root Cause**: The keyword router only checks for the exact word `"refund"`. Semantic variations, synonyms, or conversational phrasing fail to match.

### Execution 2: No Database/Customer Data Integration
* **User Query**: `"Show my subscription status"`
* **Expected Result**: System queries the database and retrieves the subscription status for the active customer.
* **Actual Output**:
  ```text
  RECEIVED QUERY: 'Show my subscription status'
  RESPONSE: 'Error: Unable to retrieve live customer records or account data. '
  ```
* **Root Cause**: The rule-based script does not possess connections to SQLite or any database query generation logic.

### Execution 3: Conversational Memory/State Failure
* **User Query Sequence**:
  1. `"My name is Janmejay"`
  2. `"What is my name?"`
* **Expected Result**: System retains context of the user's name across turns and responds with *"Your name is Janmejay"*.
* **Actual Output**:
  ```text
  RECEIVED QUERY: 'My name is Janmejay'
  RESPONSE: 'Hello! Nice to meet you.'

  RECEIVED QUERY: 'What is my name?'
  RESPONSE: 'I do not know your name. '
  ```
* **Root Cause**: The baseline agent is stateless. There is no session checkpointer or dialog state manager to pass messages or contextual variables from one interaction to the next.

---
