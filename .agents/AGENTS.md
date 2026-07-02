# Project-Specific Rules

## Implementation Plan Alignment
- **Instruction**: Always keep the active implementation plan in context before implementing, modifying, or refactoring code.
- **Reference**: Refer to the project phase implementation plan at [first_implementation_plan.md](file:///c:/Users/User/Desktop/python/capstone_project/docs/first_implementation_plan.md) to ensure all structural changes, package choices (e.g., Qdrant for vector store, local HuggingFace embeddings, Gemini Flash for LLM), and design interfaces match the approved specifications.


## Browser Verification Guardrails
- **Instruction**: Do not run browser subagents or automated browser testing automatically. Always ask the user for permission before initiating any browser-based verification or launching browser subagents.


