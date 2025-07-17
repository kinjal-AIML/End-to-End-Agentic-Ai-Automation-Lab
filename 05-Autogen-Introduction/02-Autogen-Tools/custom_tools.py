from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
import asyncio
from autogen_core.models import UserMessage

from autogen_core.tools import FunctionTool

ollama_model = OllamaChatCompletionClient(model="llama3.1")

"""
## model testing

async def main():
    response = await ollama_model.create([
        UserMessage(content="Hi, how are you?", source="user")
    ])
    print(response)
    

asyncio.run(main())
"""

## Custom tools
def reverse_string(text: str) -> str:
    """
    Reverse the user given string.
    input: str
    output: str
    """
    
    return text[::-1]

reverse_tool = FunctionTool(
    reverse_string,
    description="This tool is use for reverse the user given string."
)

agent = AssistantAgent(
    name="My_assistant",
    model_client=ollama_model,
    system_message="You are a helpful assistant that can reverse user input and given the result with summary.",
    tools=[reverse_tool],
    reflect_on_tool_use=True  ## tools result goes to the llm.
)

async def main():
    result = await agent.run(
        task="Reverse the string 'Al Amin'"
    )
    print(result)
    

if (__name__=="__main__"):
    asyncio.run(main())