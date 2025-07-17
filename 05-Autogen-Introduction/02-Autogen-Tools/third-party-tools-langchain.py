from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
import asyncio
from dotenv import load_dotenv
import os
load_dotenv()
from langchain_community.utilities import GoogleSerperAPIWrapper


os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")

ollama_model = OllamaChatCompletionClient(model="llama3.1")

search = GoogleSerperAPIWrapper()

def search_web(query: str) -> str:
    try:
        results = search.run(query)
        return results
    except Exception as e:
        print(f"Error occurred while searching the web {e}")
        return "No Such Result Found."
    
    
search_agent = AssistantAgent(
    name="SearchAgent",
    description="An agent can search the web for information",
    model_client=ollama_model,
    system_message="You are a helpful assistant that can search the web for information using the search_web tool. Please make sure that you use the search_web tool to find the information before you return the answer.",
    reflect_on_tool_use=True,
    tools=[search_web]
)

async def main():
    query = "Which team win the last BPL"
    print(query)
    
    response = await search_agent.run(task=query)
    print(f"Response: {response}")
    print("-"*20)
    print(response.messages[-1].content)
    

if __name__ == "__main__":
    asyncio.run(main())