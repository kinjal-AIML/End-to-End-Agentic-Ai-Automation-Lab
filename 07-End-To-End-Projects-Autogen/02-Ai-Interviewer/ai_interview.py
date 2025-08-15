from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core.models import UserMessage
import asyncio
from autogen_agentchat.ui import Console

model_clint = OllamaChatCompletionClient(model="llama3.1")

## Testing the model.
task = [UserMessage(content="Hi, How are you, i'm Al Amin.", source="user")]

async def get_response(task):
    response = await model_clint.create(task)
    print(response.content)
    return response

# asyncio.run(get_response(task))

## Test is end

#----------------
# Agents Define |
#----------------

# 1. Interviewer Agents
# 2. UserProxyAgent as user input
# 3. Career coach Agents

job_title = input("Enter your Job title: ")

interviewer = AssistantAgent(
    name="Interviewer",
    model_client=model_clint,
    system_message= f"""
    You are a professional interviewer specializing in {job_title} roles.
    Ask one clear question at a time and wait for the candidate's response.
    Ask 3 questions in total, covering technical skills, problem-solving abilities, and cultural fit.
    After asking 3 question, say 'TERMINATE' at the end of the interview.
    """,
    description="An interviewer agent that asks questions to the candidate."
)

interviewee = UserProxyAgent(
    name="Interviewee",
    input_func=input,
    description="A user agent that responds to interview questions."
)

career_coach = AssistantAgent(
    name="Career_Coach",
    model_client=model_clint,
    description="A career coach agent that provides guidance and advice to the candidate for a {job_title} position.",
    system_message=f"""
    you are a career coach specializing in {job_title} roles.
    Provide guidance and advice to the candidate throughout the interview process.
    after the interview, summarize the candidate's performance and provide feedback.
    """
)

team = RoundRobinGroupChat(
    participants=[interviewer, interviewee, career_coach],
    termination_condition=TextMentionTermination(text="TERMINATE"),
    max_turns=15,
    
)

stream = team.run_stream(task="Conducting an interview for a Ai Engineer position",)

async def main():
    await Console(stream)
    
    
if (__name__ == "__main__"):
    asyncio.run(main())