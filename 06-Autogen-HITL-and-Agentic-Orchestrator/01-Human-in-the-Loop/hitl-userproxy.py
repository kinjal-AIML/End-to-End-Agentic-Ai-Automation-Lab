from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
import asyncio
from dotenv import load_dotenv
import os
load_dotenv()
from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console


ollama_model_clint = OllamaChatCompletionClient(model="llama3.1")


assistant = AssistantAgent(
    name="Assistant",
    description="You are a great assistant.",
    model_client=ollama_model_clint,
    system_message="You are a really helpful assistant who help on the task given."
)




user_proxy_agent = UserProxyAgent(
    name="User_Proxy",
    description="You are a user proxy agent.",
    input_func=input
)


termination_condition = TextMentionTermination(text="APPROVE")
team = RoundRobinGroupChat(
    participants=[assistant, user_proxy_agent],
    termination_condition=termination_condition,
    max_turns=10
    
)

stream = team.run_stream(task="Write a grate poem about Bangladesh.")

async def main():
    await Console(stream)
    
if (__name__ == '__main__'):
    asyncio.run(main())