from get_model import get_ollama_model
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
import asyncio
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams
import os
from autogen_agentchat.conditions import FunctionCallTermination, TextMentionTermination
from dotenv import load_dotenv
from autogen_agentchat.ui import Console
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult
load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
model = get_ollama_model()

"""
{
    "mcpServers": {
        "serper": {
            "command": "uvx",
            "args": ["serper-mcp-server"],
            "env": {
                "SERPER_API_KEY": "<Your Serper API key>"
            }
        }
    }
}

"""

async def config():
    params = StdioServerParams(
        command="uvx",
        args=[
            "serper-mcp-server"
        ],
        env = {
                "SERPER_API_KEY": SERPER_API_KEY
            }
    )

    async with McpWorkbench(server_params=params) as workbench:
        """To get all available tools list"""
        print("----------------Tools list------------------")
        tools = await workbench.list_tools()
        print(tools)
        print("----------------Tools list------------------")

        system_prompt = """
            system_message=(
                "You are a helpful web search assistant.\n"
                "Your job: search the web and extract info based on user requests.\n"
                "Always output results in a structured, human-readable format.\n"
                "Format rules:\n"
                "- Start with a short summary.\n"
                "- Then present details in a clean JSON block.\n"
                "- Finally, say TERMINATE when you are fully done.\n"
            )

        """

        agent = AssistantAgent(
            name="web_search_boss",
            system_message=system_prompt,
            model_client=model,
            workbench=workbench,
            reflect_on_tool_use=True
        )

        team = RoundRobinGroupChat(
            participants=[agent],
            max_turns=20,
            termination_condition=TextMentionTermination("TERMINATE")
        )

        return team


async def orchestrate(team, task):
    async for msg in team.run_stream(task=task):
        yield msg



async def main():
    team = await config()
    task = (
        "Extract the best software company in Dhaka and its info, including:\n"
        "- Company name\n"
        "- Location/address\n"
        "- Chairman/CEO info\n"
        "- Social media links\n"
        "- Best product/service\n"
        "- Other relevant information"
    )

    async for msg in orchestrate(team, task):
        if isinstance(msg, TextMessage):
            if msg.source.startswith("web_search_boss"):
                print("👤 User:")
                print(msg.content)
            # elif msg.source.startswith("Data_Analyzer_Agent"):
            #     print("🤖 Data Analyzer:")
            #     print(msg.content)
            # elif msg.source.startswith("Python_Code_Executor"):
            #     print("🧑‍💻 Code Executor:")
            #     print(msg.content)

        elif isinstance(msg, TaskResult):
            print(f"\n✅ Task finished. Stop Reason: {msg.stop_reason}")


if __name__ == "__main__":
    asyncio.run(main())