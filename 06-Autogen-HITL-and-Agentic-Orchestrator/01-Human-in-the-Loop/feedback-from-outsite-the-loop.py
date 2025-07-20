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

assistant_1 = AssistantAgent(
    name="Writer",
    description="Your are responsible for Writing",
    model_client=ollama_model_clint,
    system_message="You are a grate writer who can write in less then 30 words."
)

assistant_2 = AssistantAgent(
    name="Reviewer",
    description="You are a grate Reviewer.",
    model_client=ollama_model_clint,
    system_message="Your are responsible for to review the writer agent task."
)

assistant_3 = AssistantAgent(
    name="Editor",
    description="Your are a grate Editor.",
    model_client=ollama_model_clint,
    system_message="You are a really helpful editor who can polish the content write by writer agent."
)

team_2 = RoundRobinGroupChat(
    participants=[assistant_1, assistant_2, assistant_3],
    max_turns=3
)

async def main():
    task = "Write 3 line poem about Agent."
    
    while True:
        stream = team_2.run_stream(task=task)
        await Console(stream)
        
        feedback_from_the_user_or_application = input("Please provide a feedback to the agent: ")
        if(feedback_from_the_user_or_application.lower().strip() == 'exit'):
            break
        task = feedback_from_the_user_or_application
        
        
if (__name__ == '__main__'):
    asyncio.run(main())