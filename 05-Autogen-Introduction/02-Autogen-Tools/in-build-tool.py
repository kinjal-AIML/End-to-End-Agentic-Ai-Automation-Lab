from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.tools.http import HttpTool
import asyncio

ollama_model = OllamaChatCompletionClient(model="llama3.1")

"""
{
  "fact": "A cat almost never meows at another cat, mostly just humans. Cats typically will spit, purr, and hiss at other cats.",
  "length": 116
}

"""

cat_fact_schema = {
    "type": "object",
    "properties": {
        "fact": {
            "type": "string",
            "description": "A fun or interesting fact about cats"
        },
        "length": {
            "type": "integer",
            "description": "The length of the fact string"
        }
    },
    "required": ["fact", "length"]
}


## Base tools define
http_tool = HttpTool(
    name="cat_facts_api",
    description="get cat facts",
    scheme="https",
    host="catfact.ninja",
    port=443,
    path="/fact",
    method="GET",
    json_schema=cat_fact_schema,
)

## now create a Agent
agent = AssistantAgent(
        name="My_cat_facts_Agent",
        model_client=ollama_model,
        system_message="You are helpful assistant that can provide cat facts using the cat_facts_api tool. Give the result with  summary.",
        tools=[http_tool],
        reflect_on_tool_use=True
    )



async def main():
    
    response = await agent.run(
        task="give me a random cat fact and length"
    )
    print(response.messages[-1].content)
    
if (__name__ == "__main__"):
    asyncio.run(main())