import os
import sys
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from dotenv import load_dotenv
load_dotenv()

# 1. Security: Load Key from Environment (Or default to EMPTY for local vLLM)
# api_key = os.getenv("VLLM_API_KEY", "EMPTY")

# # 2. Initialize Model with Streaming enabled
# # We use StreamingStdOutCallbackHandler to see tokens as they arrive (like ChatGPT)
# chat = ChatOpenAI(
#     model="Qwen/Qwen2.5-14B-Instruct",
#     base_url=os.getenv("BASE_URL"),
#     api_key=api_key,
#     temperature=0.7,
#     streaming=True,
#     callbacks=[StreamingStdOutCallbackHandler()] 
# )

# print("--- Starting Agentic Chat (Streamed) ---\n")

# # 3. Invocation
# messages = [
#     SystemMessage(content="You are a helpful AI assistant."),
#     HumanMessage(content="Write a 100 word paragraph about the computer.")
# ]

# # Because we enabled callbacks, this will print to console automatically
# response = chat.invoke(messages)

# print("\n\n--- Generation Complete ---")


# ----------------OPENAI SDK----------------------

from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("VLLM_API_KEY"),
    base_url=os.getenv("BASE_URL")
)

resp = client.chat.completions.create(
    model="Qwen/Qwen2.5-14B-Instruct",
    messages=[
        {"role": "system", "content": "You are a helpful AI agent."},
        {"role": "user", "content": "rite a 100 word paragraph about the computer."}
    ],
    temperature=0.2
)

print(resp.choices[0].message.content)




