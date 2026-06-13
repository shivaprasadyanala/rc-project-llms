"""
Simple ReAct Agent
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

from tools import calculator_tool, random_int_tool, geocode_tool, weather_tool, ls_tool, read_tool, write_tool, wikipedia_tool

# PROJECT: Create your own agent by adding tools and modiying the prompt
tools = [
    calculator_tool,
    random_int_tool,
    # geocode_tool,
    # weather_tool,
    # read_tool,
    # write_tool,
    # wikipedia_tool
]


# Consider adding a line at the beginning of the prompt to give the agent instructions for your specific use case
# This might help the agent perform better
PROMPT_TEMPLATE = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)


# Test agent with alternate models
LLM = "gpt-oss:20b"


def create_agent():
    agent = create_react_agent(
        llm=ChatOllama(
        model=LLM,
        base_url="http://hal9000.skim.th-owl.de:11437",
        temperature=0.9,
        top_k=70,
        reasoning=True
        ),
        tools=tools,
        prompt=PROMPT
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    )
    
    return agent_executor


def main():
    print(f"🤖 Agent with Ollama ({LLM})")
    print("=" * 60)
    print("This agent can perform calculations using the calculator tool.")
    print("Type 'exit' or 'quit' to stop.\n")
    
    agent_executor = create_agent()

    while True:
        # Get user input

        try:
            query = input("📝 Enter your query: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['exit', 'quit']:
                print("\n👋 Goodbye!")
                break
            
            print("\n" + "-" * 60)
            
            # Run the agent
            result = agent_executor.invoke({"input": query})
            
            print("-" * 60)
            print(f"✅ Final Answer: {result['output']}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()


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