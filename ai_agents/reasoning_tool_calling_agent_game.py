import json

class ReasoningAgent:

    def __init__(self, client, model):
        self.client = client
        self.model = model

    def decide(self, messages, memory):
        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a planner agent.\n"
                        "Decide next action.\n"
                        "Return ONLY JSON.\n\n"
                        "Format:\n"
                        "{\n"
                        '  "action": "tool_call | finish",\n'
                        '  "tool": "...",\n'
                        '  "args": {...},\n'
                        '  "reason": "..."\n'
                        "}\n"
                    )
                },
                {
                    "role": "system",
                    "content": f"MEMORY: {json.dumps(memory)}"
                },
                *messages
            ]
        )

        return json.loads(response.message.content)

import json
import time

class ToolAgent:

    def __init__(self, tools, max_retries=2):
        self.tools = tools
        self.max_retries = max_retries

    def run(self, tool_name, args):

        func = self.tools.get(tool_name)

        if not func:
            return {"error": f"Unknown tool: {tool_name}"}

        if isinstance(args, str):
            args = json.loads(args)

        for i in range(self.max_retries):
            try:
                result = func(**args)

                return {
                    "tool": tool_name,
                    "args": args,
                    "result": result
                }

            except Exception as e:
                print(f"[Tool retry {i}] {e}")
                time.sleep(0.2)

        return {
            "error": "Tool failed after retries",
            "tool": tool_name
        }

class AgentRunner:

    def __init__(self, reasoning_agent, tool_agent):
        self.reasoning = reasoning_agent
        self.tools = tool_agent

        self.memory = {
            "state": {},
            "last_result": None
        }

        self.messages = []

    def run(self, user_input, max_steps=10):

        self.messages.append({
            "role": "user",
            "content": user_input
        })

        for step in range(max_steps):

            # 🧠 1. Reasoning step
            decision = self.reasoning.decide(
                self.messages,
                self.memory
            )

            print("DECISION:", decision)

            # 🛑 finish condition
            if decision["action"] == "finish":
                return decision.get("reason", "Done")

            # 🔧 2. tool execution
            if decision["action"] == "tool_call":

                result = self.tools.run(
                    decision["tool"],
                    decision["args"]
                )

                print("TOOL RESULT:", result)

                # store memory
                self.memory["last_result"] = result
                self.memory["state"][decision["tool"]] = result

                # feed result back to reasoning agent
                self.messages.append({
                    "role": "tool",
                    "content": json.dumps(result)
                })

        return "Max steps reached"



def move(x, y):
    return f"Moved to {x},{y}"

def water(crop_id, amount):
    return f"Watered crop {crop_id} with {amount}"



reasoning = ReasoningAgent(client, "deepseek-r1")
tools = ToolAgent(available_tools)

runner = AgentRunner(reasoning, tools)

result = runner.run("Go water all crops nearby")
print(result)