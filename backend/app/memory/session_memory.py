# session_memory.py
from langgraph.checkpoint.memory import MemorySaver

# Shared checkpointer instance to isolate memory per thread/session
memory_checkpointer = MemorySaver()
