import asyncio
import dotenv
from langchain_core.messages import HumanMessage
from src.graph import build_graph

# Load environment variables
dotenv.load_dotenv()

async def run_chat():
    # 1. Build the graph
    bot = build_graph()

    # 2. Configure session (thread_id keeps memory)
    config = {"configurable": {"thread_id": "user_1"}}

    print("--- Chatbot Initialized (Type 'q' to quit) ---")

    while True:
        # Note: input() is blocking, but okay for a simple CLI script.
        user_input = input("\nUser: ")
        
        if user_input.lower() in ["q", "quit", "exit"]:
            print("Goodbye!")
            break

        # Prepare input state
        input_state = {"messages": [HumanMessage(content=user_input)]}

        print("AI:   ", end="", flush=True)

        # 3. ASYNC STREAMING LOGIC
        # We use 'async for' because astream_events is an asynchronous generator.
        async for event in bot.astream_events(input_state, config, version="v1"):
            
            # Filter for the specific event type from the LLM
            if event["event"] == "on_chat_model_stream":
                # Get the chunk content
                chunk = event["data"]["chunk"].content
                if chunk:
                    # Print immediately without newline
                    print(chunk, end="", flush=True)

if __name__ == "__main__":
    # We must run the async function using asyncio.run
    asyncio.run(run_chat())