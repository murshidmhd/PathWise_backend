import asyncio
import os
import sys

# Add the parent directory to sys.path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat.service import chat
from chat.schemas import ChatRequest, UserContext


async def test_director():
    print("🚀 Testing Executive LLM (Director)...")

    # 1. Test standard chat (No director steering)
    print("\n--- Test 1: Standard Chat ---")
    req_chat = ChatRequest(
        message="What is the average salary of a software engineer in India?",
        session_type="chat",
        user_context=UserContext(primary_career="Software Engineer"),
    )
    res_chat = await chat(req_chat)
    print(f"Response: {res_chat.reply}")

    # 2. Test assessment with vague input (Director should steer)
    print("\n--- Test 2: Assessment with Vague Input ---")
    req_assessment = ChatRequest(
        message="I built a web app once.",
        session_type="assessment",
        user_context=UserContext(primary_career="Software Engineer"),
    )
    res_assessment = await chat(req_assessment)
    print(f"Response: {res_assessment.reply}")


if __name__ == "__main__":
    asyncio.run(test_director())
