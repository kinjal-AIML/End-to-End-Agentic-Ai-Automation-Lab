# 🧠 Advanced LangGraph & Agentic Design: Master Reference Guide

## 1. The Core Concept: What is the "State"?
In LangGraph, the **State** is the Agent's **Internal Memory**. 
If you don't use State, an LLM is like a person with amnesia—it only knows exactly what is in the current chat prompt. The State is where we store long-term variables (like a list of messages, a virtual file system, a to-do list, or a player's inventory).

---

## 2. Tools: Real World vs. Internal Memory
A Tool is just a normal Python function that the LLM is allowed to trigger. However, how we build the tool depends on *where* the tool is doing its job.

### Scenario A: The Real World (Stateless Tools)
If a tool interacts with the outside world (like a real database, a real hard drive, or the real internet), it **does not** need the Agent's State. 
*   **Example:** A tool that reads a real file on your computer.
```python
@tool
def read_real_file(filename: str):
    # Just standard Python. No state needed.
    with open(filename, "r") as f:
        return f.read()
```

### Scenario B: Internal Memory (Stateful Tools)
**The Real-Life Example: The Virtual Shopping Cart.**
Imagine building an AI cashier. The user says *"Add an Apple to my cart."* 
The LLM generates a JSON command: `{"item": "Apple"}`.
If the tool is just a normal Python function, it will fail. Why? Because the Python function doesn't know where the cart is! The cart is a variable inside the LangGraph State. To let the Python function see the cart, we must **Inject the State**.

---

## 3. Injecting State (`InjectedState`)
`InjectedState` is a magic tag that tells LangGraph: *"Do not show this argument to the LLM. When the LLM triggers this tool, automatically sneak the current Graph State into the function so Python can use it."*

**The Real-Life Example: The Video Game NPC.**
Your agent plays an RPG. The State holds `gold` and `inventory`.
*   **What the LLM sees:** `buy_item(item_name="Sword", cost=50)`
*   **What Python sees:** `buy_item(item_name="Sword", cost=50, state=PlayerState)`

This is incredibly powerful because **Python can enforce the rules that the LLM might hallucinate.**

```python
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

@tool
def buy_item(item_name: str, cost: int, state: Annotated[PlayerState, InjectedState]):
    # 1. Python secretly reads the Agent's memory
    current_gold = state.get("gold", 0)
    current_inventory = state.get("inventory", [])
    
    # 2. Python enforces the rules!
    if current_gold < cost:
        return f"Error: You only have {current_gold} gold. Can't afford {item_name}."
    
    # 3. If valid, update the memory variables
    return Command(
        update={
            "gold": current_gold - cost,
            "inventory": current_inventory + [item_name]
        }
    )
```

**Pro-Tip: Injecting just one variable.** 
If you only need one variable (e.g., just `gold`), you can inject it directly:
`current_gold: Annotated[int, InjectedState("gold")]`

---

## 4. Manual Control (`Command` & `ToolMessage`)
Normally, a tool just returns a string (e.g., `return "Success!"`). When it does this, LangGraph operates as a "Black Box": it automatically wraps your string in a `ToolMessage` and gives it to the LLM.

However, when you return `Command(update={...})`, you take **Manual Control** to change variables in the State. Because you took manual control, LangGraph stops doing things automatically. Therefore, **you must manually pass the ToolMessage back to the LLM** so the LLM isn't left waiting blindly.

```python
from langchain_core.tools import InjectedToolCallId
from langchain_core.messages import ToolMessage

@tool
def my_tool(arg: str, tool_call_id: Annotated[str, InjectedToolCallId]):
    return Command(
        update={
            "my_custom_variable": "new_data", # 1. Update your memory variable
            "messages": [
                # 2. MUST manually return the message so the LLM sees the result!
                ToolMessage("Tool finished successfully", tool_call_id=tool_call_id)
            ]
        }
    )
```

---

## 5. Reducers: The "Bouncers" of Memory
When a tool finishes, it brings a box of "New Data" to the Agent's Memory. A **Reducer** is the Bouncer at the door. The Bouncer looks at the "Old Data" (`left`) and the "New Data" (`right`) and decides how to combine them.

If you don't define a reducer, the default behavior is **OVERWRITE** (throw away the old data).

### Reducer Type A: The List Reducer (Append)
**The Real-Life Example: The Restaurant Receipt.**
You order a Pizza, then a Coke. You want the waiter to *add* the Coke to the bill, not erase the Pizza.

```python
def reduce_list(left: list | None, right: list | None) -> list:
    if not left: left = []
    if not right: right = []
    return left + right  # Append them together!
```
*   **Data Flow Step 1:** Memory (`left`) is `["(add, 5, 3)"]`. Tool (`right`) brings `["(multiply, 2, 4)"]`.
*   **Result:** `["(add, 5, 3)", "(multiply, 2, 4)"]`. The history is safely appended!

### Reducer Type B: The Dictionary Reducer (Merge)
**The Real-Life Example: The Smartphone Contact Book.**
1. You meet Bob -> Add him (Don't delete everyone else).
2. Alice changes her number -> Overwrite Alice's old number, keep everyone else.

```python
def file_reducer(left, right):
    if left is None: return right
    elif right is None: return left
    else: return {**left, **right} # Unpack and merge!
```
*   **Data Flow Step 1:** Memory (`left`) has `{"file_A.txt": "Hello"}`. Tool (`right`) brings `{"file_B.txt": "World"}`.
    *   *Result:* `{**left, **right}` creates `{"file_A.txt": "Hello", "file_B.txt": "World"}`. (Bob was added).
*   **Data Flow Step 2:** Memory (`left`) has `{"file_A.txt": "Hello"}`. Tool (`right`) brings `{"file_A.txt": "Goodbye"}`.
    *   *Result:* Because the keys match, the one on the right wins. `{"file_A.txt": "Goodbye"}`. (Alice's number was updated).

---

## 6. Advanced Agentic Patterns
Finally, *why* do we do all this? To protect the LLM's brain (Context Window).

### Pattern A: Context Offloading (Virtual File System)
If an agent downloads a 10,000-word Wikipedia article, shoving that into the chat `messages` will bloat the LLM's memory. Instead, we **offload** it to the Graph State using a `write_file` tool. It lives safely in the `files` dictionary (our Contact Book/Merge reducer), out of the LLM's immediate brain.

### Pattern B: Pagination (`read_file`)
When the LLM finally needs to read that huge file, we force it to read in chunks using `offset` and `limit` (e.g., "Read lines 0 to 500"). This prevents the LLM from getting overwhelmed and hallucinating.

### Pattern C: Mission Focus (TODO Lists)
When an agent runs for 50+ steps, it forgets its original goal. We create a `todos` list in the state with **NO REDUCER** (Overwrite mode). Every few steps, the agent rewrites its whole to-do list, deleting finished items and adding new ones. This forces its current goals to stay fresh at the very bottom of the chat context. 

---
### Summary Cheat Sheet for State Design

| How you define it in Python | Reducer Type | What happens to the data? | Best Used For |
| :--- | :--- | :--- | :--- |
| `todos: list` | **None** | **OVERWRITE.** Old data is destroyed. | Todo lists, current status flags. |
| `ops: Annotated[list, reduce_list]` | **Append** | **ADD TO END.** Old data kept, new data appended. | Chat histories (`messages`), math operation logs. |
| `files: Annotated[dict, file_reducer]`| **Merge** | **UPDATE/ADD.** Old keys kept, new keys added, matching keys overwritten. | Virtual file systems, game inventories. |