from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
import asyncio
from autogen_core.models import UserMessage

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
    
    
async def main():
    response = await ollama_model_client.create([UserMessage(content="Assalamualikum sir.", source="user")])
    print(response)
    await ollama_model_client.close()
    
if (__name__ == "__main__"):
    asyncio.run(main())
