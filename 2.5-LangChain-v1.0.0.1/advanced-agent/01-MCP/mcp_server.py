# import os
# from dotenv import load_dotenv
# load_dotenv()
# from langchain.agents import create_agent
# from mcp.server.fastmcp import FastMCP
# from tavily import TavilyClient
# from typing import Dict, Any
# from requests import get

# os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")

# from langchain.chat_models import init_chat_model

# model = init_chat_model("gpt-4.1-mini")

# mcp = FastMCP[Any]("mcp_server")
# tavily_clint = TavilyClient()

# ## Tools for searching Web
# @mcp.tool()
# def web_search(query: str) -> Dict[str, Any]:
#     """Search the web for information."""
#     return tavily_clint.search(query)

# # resource - provide access to langchin-ai repo file
# @mcp.resource("d2ll://LoRA")
# def github_file():
#     """Resource for accessing md al amin git repo file..."""
#     url = "https://raw.githubusercontent.com/MDalamin5/Data2llm-16-Personality-MBTI-Prediction-Pipeline-RAG-LoRA/refs/heads/main/README.md"
#     try:
#         resp = get(url)
#         return resp.text
    
#     except Exception as e:
#         return f"Error: {str(e)}"
    

# @mcp.prompt()
# def prompt():
#     """Analyze data from a Md Al Amin repo file with comprehensive insights"""
#     return """
#     You are a helpful assistant that answer user questions about Lora, Fine-tune, MITB.
#     you can use the following tools/resources to answer user questions:
#     - search_web: Search the web for information
#     - github_file: Access the mdalmin5 repo file.

#     if the user asks a questions that is not related to deep learning, ml you should say I'm sorry its out of my capicity.
#     you may try multiple tool and resource call to anser the user's questions.
#     """

# if __name__ == "__main__":
#     print("Server is running...")
#     mcp.run(transport="stdio")


import os
from dotenv import load_dotenv
from typing import Dict, Any
from requests import get

from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

from langchain.chat_models import init_chat_model

# Load env
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Model (used by agent later)
model = init_chat_model("gpt-4.1-mini")

# MCP server
mcp = FastMCP[Any]("mcp_server")

tavily_client = TavilyClient()

# -----------------------------
# TOOL
# -----------------------------
@mcp.tool()
def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information."""
    return tavily_client.search(query)

# -----------------------------
# RESOURCE
# -----------------------------
@mcp.resource("repo://lora/readme")
def github_lora_readme():
    """README from Md Al Amin's LoRA repo"""
    url = (
        "https://raw.githubusercontent.com/"
        "MDalamin5/Data2llm-16-Personality-MBTI-Prediction-Pipeline-RAG-LoRA/"
        "refs/heads/main/README.md"
    )
    try:
        resp = get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Error fetching README: {str(e)}"

# -----------------------------
# PROMPT
# -----------------------------
@mcp.prompt()
def prompt():
    return """
You are a helpful assistant specialized in:
- LoRA
- Fine-tuning
- Deep Learning
- Machine Learning
- RAG systems

You can use:
- web_search tool
- repo://lora/readme resource

If the question is NOT related to ML or DL,
politely say it is out of your capacity.
"""

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    print("MCP Server running...")
    mcp.run(transport="stdio")
