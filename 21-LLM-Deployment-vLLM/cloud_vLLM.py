# import os
# import sys
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_core.callbacks import StreamingStdOutCallbackHandler
# from dotenv import load_dotenv
# load_dotenv()

# # 1. Security: Load Key from Environment (Or default to EMPTY for local vLLM)
# api_key = os.getenv("VLLM_API_KEY", "EMPTY")

# # 2. Initialize Model with Streaming enabled
# # We use StreamingStdOutCallbackHandler to see tokens as they arrive (like ChatGPT)
# chat = ChatOpenAI(
#     model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
#     base_url="https://3k4shnbxnqlza2-8001.proxy.runpod.net/v1",
#     api_key=os.getenv("VLLM_API_KEY"),
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


import os
import sys
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
# 1. Update this with your NEW RunPod ID from the dashboard
POD_ID = "3k4shnbxnqlza2" 
BASE_URL = f"https://{POD_ID}-8001.proxy.runpod.net/v1"

# 2. Magic Model Name
# Because your start.sh uses '--served-model-name "default"',
# we can use "default" here. It will automatically use Qwen, TinyLlama, or whatever is running!
MODEL_NAME = "default"

# 3. Initialize Chat
chat = ChatOpenAI(
    model=MODEL_NAME,
    base_url=BASE_URL,
    # Since you didn't set VLLM_API_KEY on RunPod, this can be anything.
    api_key=os.getenv("VLLM_API_KEY"), 
    temperature=0.7,
    max_tokens=500,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()] 
)

print(f"--- 🚀 Connecting to Agentic Brain ({MODEL_NAME}) ---\n")

# 4. Invocation
messages = [
    SystemMessage(content="You are an intelligent AI assistant capable of complex reasoning. Make sure your output format is markdown."),
    HumanMessage(content="Write a 1000 word paragraph about the future of AI Agents.")
]

try:
    # This will stream the output directly to your console
    response = chat.invoke(messages)
    print("\n\n✅ Generation Complete")
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    print("Tip: Check if POD_ID is correct and the pod is fully running (wait 60s after start).")



# output:

"""
--- 🚀 Connecting to Agentic Brain (default) ---

## The Future of AI Agents

The future of Artificial Intelligence (AI) agents promises to be transformative, reshaping our understanding and interaction with technology in profound ways. As we move forward into an era where machine learning and deep neural networks become increasingly sophisticated, AI agents will evolve from mere tools to sophisticated companions that can adapt, learn, and interact with humans in more nuanced and personalized ways. This evolution is not just about improving efficiency or accuracy; it's about creating a new paradigm of human-computer interaction that is more empathetic, intuitive, and seamless.

One of the key areas of advancement in AI agents will be their ability to understand and respond to human emotions. Current AI systems often struggle with recognizing subtle emotional cues, leading to interactions that can feel cold or mechanical. However, as AI agents gain access to larger datasets and more advanced natural language processing capabilities, they will become better at interpreting tone, facial expressions, and even body language. This enhanced emotional intelligence will enable AI agents to provide more empathetic support, whether in therapeutic settings, customer service scenarios, or everyday conversations. For instance, an AI therapist could use these advanced emotional recognition skills to offer tailored advice based on a patient’s current emotional state, potentially revolutionizing mental health care by making it more accessible and personalized.

Moreover, the integration of AI agents into various aspects of daily life will lead to significant improvements in productivity and convenience. Imagine a world where AI agents can seamlessly integrate with smart homes, wearable devices, and personal assistants to create a cohesive digital ecosystem that anticipates and responds to individual needs. For example, an AI agent could monitor a person's health data from wearables, recognize early signs of illness, and proactively recommend preventive measures or schedule appointments with healthcare providers. This level of proactive assistance has the potential to transform how we manage our health, making it more efficient and effective.

In the professional realm, AI agents will play an increasingly crucial role in automating routine tasks, freeing up time for more creative and strategic work. For instance, in industries such as finance, law, and engineering, AI agents could handle data entry, document review, and preliminary analysis, allowing professionals to focus on higher-value tasks that require critical thinking and decision-making. Furthermore, AI agents could facilitate more efficient communication and collaboration among team members by summarizing meeting notes, scheduling follow-ups, and even suggesting next steps based on project timelines and priorities. This not only enhances productivity but also reduces the cognitive load on individuals, potentially leading to less

✅ Generation Complete

"""