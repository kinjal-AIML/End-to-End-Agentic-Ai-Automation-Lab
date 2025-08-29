from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core.models import UserMessage, ModelInfo
import asyncio
import time

# ---Model latency Testing ---

# Define the model information for your custom model
gpt_oss_model_info = ModelInfo(
    family="gpt-oss",  # Or any other appropriate family name
    vision=False,
    function_calling=False,  # Set to True if your model supports it
    json_output=False  # Set to True if your model supports it
)

ollama_model_clint = OllamaChatCompletionClient(
    model="gpt-oss:20b",
    model_info=gpt_oss_model_info
)

messages = [UserMessage(content="What is ML?", source="user")]

async def main():
    # start = time.time()
    response = await ollama_model_clint.create(messages)
    # end = time.time()
    print(response)
    # print(tt = end-start)

if __name__ == "__main__":
    asyncio.run(main())