from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core.models import UserMessage, ModelInfo
import asyncio


# ---Model latency Testing ---

# Define the model information for your custom model
gpt_oss_model_info = ModelInfo(
    family="gpt-oss",  # Or any other appropriate family name
    vision=False,
    function_calling=False,  # Set to True if your model supports it
    json_output=False  # Set to True if your model supports it
)
def get_ollama_model():
    # ollama_model_clint = OllamaChatCompletionClient(
    #     model="gpt-oss:20b",
    #     model_info=gpt_oss_model_info
    # )
    ollama_model_clint = OllamaChatCompletionClient(model="llama3.1")
    return ollama_model_clint

messages = [UserMessage(content="What is ML?", source="user")]

async def main():
    # start = time.time()
    response = await get_ollama_model().create(messages)
    # end = time.time()
    print(response)
    # print(tt = end-start)

if __name__ == "__main__":
    asyncio.run(main())