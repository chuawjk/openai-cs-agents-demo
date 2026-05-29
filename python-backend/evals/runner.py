import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from uuid import uuid4

from agents import Runner
from airline.agents import triage_agent
from airline.context import AirlineAgentChatContext, create_initial_context
from chatkit.types import ThreadMetadata
from memory_store import MemoryStore


async def get_agent_response(user_input: str) -> str:
    store = MemoryStore()
    thread = ThreadMetadata(id=uuid4().hex, created_at=datetime.now())
    ctx = AirlineAgentChatContext(
        thread=thread,
        store=store,
        request_context={},
        state=create_initial_context(),
    )
    result = await Runner.run(triage_agent, user_input, context=ctx)
    return result.final_output or ""
