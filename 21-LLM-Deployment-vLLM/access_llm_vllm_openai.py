# Command to host llm via vllm and accessing through the Openai SDK
# vllm serve TinyLlama/TinyLlama-1.1B-Chat-v1.0 --gpu_memory_utilization 0.6 --api_key "Your api key hare..."

# from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# client = OpenAI(
#     base_url="http://localhost:8000/v1",
#     api_key=os.getenv("VLLM_API_KEY")
# )

# response = client.chat.completions.create(
#     model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
#     messages=[
#         {
#             "role": "system", "content": "Your are a good ai assistant."
#         },
#         {
#             "role": "user", "content": "Summarize the ideas about the CSE degree in simple word."
#         }
#     ]
# )

# print(response.choices[0].message.content)

# ------v1------------
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(base_url="http://localhost:8000/v1", api_key=os.getenv("VLLM_API_KEY"), model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")

response = llm.invoke("Hi sir how are you")

print(response.content)


