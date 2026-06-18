import json
import time


class AgentState:
    def __init__(self):
        self.messages = []
        self.memory = {
            "position": None,
            "inventory": {},
            "world_state": {},
            "last_tool_result": None
        }

    def add_message(self, msg):
        self.messages.append(msg)

    def update_memory(self, key, value):
        self.memory[key] = value

        
class ToolExecutor:

    def __init__(self, tools, max_retries=2):
        self.tools = tools
        self.max_retries = max_retries

    def execute(self, tool_call):
        name = tool_call.function.name
        args = tool_call.function.arguments

        func = self.tools.get(name)

        if not func:
            return {"error": f"Unknown tool: {name}"}

        # Ollama sometimes returns string args → normalize
        if isinstance(args, str):
            args = json.loads(args)

        for attempt in range(self.max_retries):
            try:
                result = func(**args)
                return {
                    "tool": name,
                    "args": args,
                    "result": result
                }

            except Exception as e:
                print(f"[Retry {attempt}] Tool failed: {e}")
                time.sleep(0.2)

                # simple self-correction hook
                args = self._repair_args(args, str(e))

        return {"error": "Tool failed after retries"}

    def _repair_args(self, args, error):
        """
        lightweight correction strategy
        (you can replace this with an LLM later)
        """
        if isinstance(args, dict):
            # example fallback: remove bad keys
            return {k: v for k, v in args.items() if v is not None}

        return args


def run_agent(client, model, system_prompt, tools, state: AgentState, max_steps=10):

    executor = ToolExecutor(tools)

    for step in range(max_steps):

        messages = build_messages(system_prompt, state)

        response = client.chat(
            model=model,
            messages=messages,
            tools=tools
        )

        msg = response.message

        # store everything
        state.add_message(msg)

        # 1. normal response (final answer or reasoning)
        if msg.content:
            print("LLM:", msg.content)

        # 2. tool calls
        if msg.tool_calls:

            for tool_call in msg.tool_calls:

                print(f"Calling tool: {tool_call.function.name}")

                result = executor.execute(tool_call)

                state.memory["last_tool_result"] = result

                # feed result back to LLM as observation
                state.add_message({
                    "role": "tool",
                    "content": json.dumps(result)
                })

                # optional: update structured memory
                if "result" in result:
                    state.update_memory(
                        "world_state",
                        result["result"]
                    )

        # stopping condition (LLM decides it's done)
        if msg.content and "FINAL" in msg.content.upper():
            break

    return state

def build_messages(system_prompt, state: AgentState):
    return [
        {"role": "system", "content": system_prompt},

        # memory injection
        {
            "role": "system",
            "content": f"MEMORY: {json.dumps(state.memory)}"
        },

        *state.messages
    ]

def compress_memory(state):
    state.memory = {
        "summary": "...",
        "key_state": state.memory["world_state"]
    }

        #   Reasoning LLM
        #         ↓
        # Plan / Tool Call
        #         ↓
        # Tool Executor (safe)
        #         ↓
        # Retry + Repair layer
        #         ↓
        #     Memory update
        #         ↓
        # Back to LLM


