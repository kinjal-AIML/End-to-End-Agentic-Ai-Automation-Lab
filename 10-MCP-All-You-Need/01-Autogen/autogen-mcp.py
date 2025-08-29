from ollama_model_clint import get_ollama_model
from autogen_agentchat.agents import AssistantAgent
import asyncio
import time
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

# What is Workbench?
"""
 ---Answer: A
    A Workbench than wraps an MCP server and provides an interface to list and call tools provided by the server.
   
    The workbench should be used as a context manager to ensure proper initialization and cleanup of the underlying MCP session. ---

"""
# --- StdioServerParams() is same as the build in MCP server

"""
---This build in Time MCP server---

"my-mcp-server-a28dde86": {
			"type": "stdio",
			"command": "uvx",
			"args": [
				"mcp-server-time"
			]
		}

"""

async def main():
    params = StdioServerParams(
        command="uvx",
        args=[
            "mcp-server-time",
            "--local-timezone=America/New_York"
        ]
    )
    model = get_ollama_model()

    async with McpWorkbench(server_params=params) as workbench:
        agent = AssistantAgent(
            name="get_time_agent",
            system_message="You are helpful assistant. You have time mcp server to get current time based on the locations.",
            model_client=model,
            workbench=workbench
        )

        task = "What is the time right now in Dhaka."

        async for msg in agent.run_stream(task=task):
            print("-"*50)
            print(msg)
            print("-"*50)


if __name__ == "__main__":
    asyncio.run(main())