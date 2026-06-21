"""
Simple ReAct Agent
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
import json
# from tools import calculator_tool, random_int_tool, geocode_tool, weather_tool, ls_tool,read_tool, write_tool, wikipedia_tool,astar_tool,collect_water_tool,water_tool,plant_crop_tool,move_tool,crops_to_text,nstate
from tools import astar,collect_water,water,plant_crop,move,crops_to_text,nstate,state,moves,points,points_object
import requests
from langchain.callbacks.base import BaseCallbackHandler
import time
import logging
logger = logging.getLogger(__name__)
log_file_name = "react_langchain_log.log"

logging.basicConfig(filename=log_file_name, encoding='utf-8', level=logging.INFO,format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True
tools = [astar,collect_water,water,plant_crop,move]

def format_tools(tools):
    formatted = []
    for t in tools:
        formatted.append(f"""
        Tool Name: {t.name}
        Description: {t.description}
        Args Schema: {t.args if hasattr(t, 'args') else 'unknown'}
        """)
    return "\n".join(formatted)

# print(format_tools(tools))
# breakpoint()
world_state = nstate



tool_names = ["water","collect_water","plant_crop","move","astar"]
# PROMPT_TEMPLATE = """
# You are a smart farm game agent.

# Your objective is to complete all farming tasks by using the available tools.

# Available tools (STRICT SCHEMA):
# {tools}

# ==================================================
# WORLD STATE
# ==================================================

# {world_state}

# RULES
# ==================================================

# - Use tools to interact with the environment.
# - Never describe a move when a move tool exists.
# - Never output tool arguments as Python function syntax (e.g., do NOT do tool_name(arg=val)).
# - If a tool requires multiple arguments, ALWAYS provide them as a valid raw JSON object in the Action Input.
# - If an action is required, call a tool.
# - Move only 25 pixels at a time.
# - Move in one direction per move.
# - Do not move diagonally.
# - Crops cannot be traversed.
# - Always check crop status before planting.
# - A crop can only be water if it is planted.
# - If water is unavailable, collect water first.
# - Use astar_tool whenever navigation is needed.
# - Follow the returned path one step at a time.
# - Never manually calculate distances.
# - Before watering the crop must check if the crop is planted.
# - Before giving Final Answer:
#     - Verify every crop has planted=True
#     - Verify every crop has needs_water=False
# - Continue until all crops are planted and watered.
# - ALWAYS follow tool argument schema exactly
# - NEVER convert arguments into natural language
# - NEVER merge multiple fields into one string
# - ALWAYS pass all required fields

# ==================================================
# REACT FORMAT
# ==================================================

# Thought: reason about the current state
# Action: one of [{tool_names}]
# Action Input: A JSON object containing the tool arguments matching the schema exactly (e.g., {{"param1": value, "param2": value}})
# Observation: tool result

# (repeat as needed)

# When all crops are completed:

# Thought: I have verified that all crops are planted and watered.
# Final Answer: Task completed successfully.

# Begin!

# Question: Complete the farming task.

# Thought: {agent_scratchpad}
# """

PROMPT_TEMPLATE = """
You are a smart farm game agent.

Your objective is to complete all farming tasks by using the available tools.

Available tools (STRICT SCHEMA):
{tools}

==================================================
WORLD STATE
==================================================

{world_state}

RULES
==================================================
1. MOVEMENT: 
   - Move only 25 pixels at a time, in one direction per move (no diagonals).
   - Use astar_tool whenever navigation is needed and follow the path strictly. Never calculate distances manually.
   - You cannot traverse over crops.

2. FARMING SEQUENCE (STRICT):
   - Step 1: Collect water using collect_water_tool (if you don't have any).
   - Step 2: Plant the crop using plant_crop tool.
   - Step 3: Water the crop using water tool.
   - CRITICAL: You CANNOT water a crop until you have planted it. Always check crop status.

3. TOOL FORMATTING:
   - Always output tool arguments as a valid JSON object in the Action Input.
   - NEVER use Python function syntax (e.g., do NOT do tool_name(arg=val)).
   - NEVER convert arguments into natural language.

==================================================
REACT FORMAT
==================================================

Thought: reason about the current state
Action: one of [{tool_names}]
Action Input: A JSON object containing the tool arguments matching the schema exactly (e.g., {{"param1": value, "param2": value}})
Observation: tool result

(repeat as needed)

When all crops are completed:

Thought: I have verified that all crops are planted and watered.
Final Answer: Task completed successfully.

Begin!

Question: Complete the farming task.

Thought: {agent_scratchpad}

Think step by step.
"""
PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)


# Test agent with alternate models
# LLM = "gpt-oss:20b"
# LLM = "gemma4:26b"
# LLM = "glm-4.7-flash:q4_K_M"
# LLM = "qwen3.6:27b"
# LLM = "llama3.3:70b-instruct-q8_0"
LLM = "nemotron3:33b"

llm_call_times = []

class DetailedTimingCallback(BaseCallbackHandler):
    def __init__(self):
        self.llm_start = None
        self.tool_start = None

    def on_llm_start(self, *args, **kwargs):
        self.llm_start = time.perf_counter()

    def on_llm_end(self, *args, **kwargs):
        print(
            f"LLM took {time.perf_counter() - self.llm_start:.3f}s"
        )
        time_taken = time.perf_counter() - self.llm_start
        llm_call_times.append(time_taken)

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.tool_start = time.perf_counter()
        print(f"Starting tool: {serialized['name']}")

    def on_tool_end(self, output, **kwargs):
        print(
            f"Tool took {time.perf_counter() - self.tool_start:.3f}s"
        )



def create_agent():
    callback = DetailedTimingCallback()
    agent = create_react_agent(
        llm=ChatOllama(
        model=LLM,
        base_url="http://hal9000.skim.th-owl.de:11437",
        temperature=0.1,
        top_k=70,
        reasoning=False,
        callbacks=[callback],
        validate_model_on_init=True
        )
        ,
        tools=tools,
        # prompt=PROMPT
        prompt = PROMPT.partial(
            tools=format_tools(tools),
            tool_names=[t.name for t in tools]
        )
    )
   
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=100,
        callbacks=[callback],
        handle_parsing_errors=True,
    )
    
    return agent_executor


def main():
    print(f"🤖 Agent with Ollama ({LLM})")
    print("=" * 60)
    print("This agent can perform calculations using the calculator tool.")
    print("Type 'exit' or 'quit' to stop.\n")
    
    agent_executor = create_agent()
    query = "plant crops and water them. thank you."
    new_crops = {}
    while True:
        try:
            
            result = agent_executor.invoke({"input": query,"world_state":world_state})
            
            # print(result["output"])
            if state["goal_completed"] == True:
                print("moves:")
                print(moves)
                logger.info(f"player moves: {moves}")

                print("points gain:")
                print(points_object["points"])
                logger.info(f"points gain: {points_object['points']}")
                
                print("llm call times")
                print(llm_call_times)
                logger.info(f"llm calls: {llm_call_times}")
                
                print("len of llm calls:")
                print(len(llm_call_times))
                logger.info(f"len of llm calls: {len(llm_call_times)}")
                break
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()


# Use astar to find the path to your target.

# astar will return a list of coordinates.

# Immediately pass that entire list of coordinates into the follow_path tool to travel there.

# Never attempt to move step-by-step manually.

# from pydantic import BaseModel, Field, ValidationError
# from typing import Dict

# class MoveArgs(BaseModel):
#     dx: int = Field(ge=0)
#     dy: int = Field(ge=0)



# class PlantCropArgs(BaseModel):
#     dx: int = Field(ge=0)
#     dy: int = Field(ge=0)

# class Crop(BaseModel):
#     pos: list[int]
#     needs_water: bool
#     planted: bool

# class GameState(BaseModel):
#     grid_size: list[int]
#     player_pos: list[int]
#     crops: Dict[str, Crop]
#     water_available: bool
#     goal_completed: bool

# tool_schemas = {
#     "move": MoveArgs,
#     "plant_crop": PlantCropArgs,
# }
# schema = tool_schemas[tool_call.function.name]

# try:
#     validated_args = schema.model_validate(
#         tool_call.function.arguments,
#         strict=True
#     )

#     result = function_to_call(
#         **validated_args.model_dump1()
#     )

# except ValidationError as e:
#     result = {
#         "success": False,
#         "error": str(e)
#     }


# validated_state = GameState.model_validate(
#     new_state
# )















# try:
#     args = MoveArgs.model_validate(
#         tool_call.function.arguments
#     )

#     result = move(
#         dx=args.dx,
#         dy=args.dy
#     )

# except ValidationError as e:
#     result = f"Invalid arguments: {e}"





# MoveArgs.model_validate(
#     tool_call.function.arguments,
#     strict=True
# )