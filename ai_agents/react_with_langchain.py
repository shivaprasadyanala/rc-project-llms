from langchain_community.llms import Ollama
from langchain.agents import create_agent, Tool
from langchain.agents import AgentType
from langchain.prompts import PromptTemplate
import math

# --- Define a simple tool the agent can use ---
def calculate_square_root(number_str: str) -> str:
    """Calculate the square root of a number."""
    try:
        num = float(number_str)
        if num < 0:
            return "Error: Cannot take square root of a negative number."
        return f"The square root of {num} is {math.sqrt(num):.4f}"
    except ValueError:
        return "Error: Please provide a valid number."

tools = [
    Tool(
        name="SquareRootCalculator",
        func=calculate_square_root,
        description="Use this to calculate the square root of a number."
    )
]

# --- Initialize Ollama LLM ---
llm = Ollama(model="llama3", temperature=0)

# --- Create the ReAct agent ---
agent = create_agent(
    tools = [calculate_square_root],
    model = llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # ReAct-style reasoning
    verbose=True
)

# --- Run the agent ---
if __name__ == "__main__":
    query = "What is the square root of 144?"
    result = agent.run(query)
    print("\nFinal Answer:", result)


from pydantic import BaseModel, Field, ValidationError
from typing import Dict

class MoveArgs(BaseModel):
    dx: int = Field(ge=0)
    dy: int = Field(ge=0)



class PlantCropArgs(BaseModel):
    dx: int = Field(ge=0)
    dy: int = Field(ge=0)

class Crop(BaseModel):
    pos: list[int]
    needs_water: bool
    planted: bool

class GameState(BaseModel):
    grid_size: list[int]
    player_pos: list[int]
    crops: Dict[str, Crop]
    water_available: bool
    goal_completed: bool

tool_schemas = {
    "move": MoveArgs,
    "plant_crop": PlantCropArgs,
}
schema = tool_schemas[tool_call.function.name]

try:
    validated_args = schema.model_validate(
        tool_call.function.arguments,
        strict=True
    )

    result = function_to_call(
        **validated_args.model_dump()
    )

except ValidationError as e:
    result = {
        "success": False,
        "error": str(e)
    }


validated_state = GameState.model_validate(
    new_state
)
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