from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
import asyncio
from autogen_core.models import UserMessage, ModelInfo

# Assuming your Ollama server is running locally on port 11434.
ollama_model_client = OllamaChatCompletionClient(
        model="llama3.1",
        host="http://127.0.0.1:11434/"
    )


    
def get_model_clint():
    ollama_model_client = OllamaChatCompletionClient(
        model="llama3.1",
        host="http://127.0.0.1:11434/"
    )
    return ollama_model_client

gpt_oss_model_info = ModelInfo(
    family="gpt-oss",  # Or any other appropriate family name
    vision=False,
    function_calling=False,  # Set to True if your model supports it
    json_output=False  # Set to True if your model supports it
)
def get_ollama_model():
    ollama_model_clint = OllamaChatCompletionClient(
        model="gpt-oss:20b",
        host="http://127.0.0.1:11434/",
        model_info=gpt_oss_model_info
    )
    # ollama_model_clint = OllamaChatCompletionClient(model="llama3.1")
    return ollama_model_clint
    
    
async def main():
    response = await ollama_model_client.create([UserMessage(content="Assalamualikum sir.", source="user")])
    print(response)
    await ollama_model_client.close()
    
if (__name__ == "__main__"):
    asyncio.run(main())
