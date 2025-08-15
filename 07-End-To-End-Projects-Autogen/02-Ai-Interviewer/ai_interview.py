from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core.models import UserMessage
import asyncio

model_clint = OllamaChatCompletionClient(model="qwen2.5:14b")

## Testing the model.
task = [UserMessage(content="Hi, How are you, i'm Al Amin.", source="user")]

async def get_response(task):
    response = await model_clint.create(task)
    print(response.content)
    return response

asyncio.run(get_response(task))

## Test is end