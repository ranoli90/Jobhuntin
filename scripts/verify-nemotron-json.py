
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../packages")))

from pydantic import BaseModel
from shared.config import get_settings

from backend.llm.client import LLMClient


class TestResponse(BaseModel):
    message: str
    score: int
    tags: list[str]

async def main():
    settings = get_settings()
    print(f"Testing model: {settings.llm_model} via {settings.llm_api_base}")

    client = LLMClient(settings)

    prompt = """
    Analyze this text: "The weather is sunny and the temperature is 75 degrees."
    Return a JSON object with:
    - message: a summary
    - score: a positivity score 1-10
    - tags: list of keywords
    """

    try:
        print("Sending request...")
        response = await client.call(
            prompt=prompt,
            response_format=TestResponse
        )
        print("\n✅ Success! Parsed JSON:")
        print(response.model_dump_json(indent=2))
    except Exception as e:
        print(f"\n❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
