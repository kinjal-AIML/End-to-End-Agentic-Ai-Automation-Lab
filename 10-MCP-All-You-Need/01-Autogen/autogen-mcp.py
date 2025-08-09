from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
import asyncio
import time
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams