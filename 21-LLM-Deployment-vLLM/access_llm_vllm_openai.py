# Command to host llm via vllm and accessing through the Openai SDK
# vllm serve TinyLlama/TinyLlama-1.1B-Chat-v1.0 --gpu_memory_utilization 0.6 --api_key "Your api key hare..."

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="alaminkey"
)

response = client.chat.completions.create(
    model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    messages=[
        {
            "role": "system", "content": "Your are a good ai assistant."
        },
        {
            "role": "user", "content": "Summarize the ideas about the CSE degree in simple word."
        }
    ]
)

print(response.choices[0].message.content)