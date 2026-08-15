
state = {
    "grid_size": (800, 600),

    # Player
    "player_pos": [200, 100],  # use list for mutability

    # Crops indexed by position
    "crops": {
        (400, 275): {"name": "wheat", "planted": False, "needs_water": True},
        (300, 200): {"name": "rice", "planted": False, "needs_water": True},
    },

    # Obstacles as a set for fast lookup
    "obstacles": [[250, 100]],
    "water_available": False,
    "water_tank": [75, 250],

    # Goal tracking
    "goal_completed": False
}


def crops_to_text(crops):
    lines = []
    for pos, info in crops.items():
        lines.append(f"- {pos}: needs_water = {info['needs_water']}")
    return "\n".join(lines)


tools_description = """
Tools available:
- follow_path(start_px, goal_px, obstacles_px): Move along the full path by calling astar.
  start_px and goal_px are [x, y] pixel coordinates; obstacles_px is a list of
  [x, y] obstacles to avoid. Use this for ALL movement.
  Returns the path from start_px to goal_px, avoiding obstacles_px.
  Pass integers, not strings. Do NOT include the goal in obstacles_px.
- collect_water(): Collect water at the water tank (75,250). Only works when
  the player is standing exactly on (75,250).
- plant_crop(x: int, y: int): Plant the crop at the player's current position.
- water(): Water the crop the player is currently standing on. Only succeeds
  when the crop is planted and water_available=True.
"""

system_message1 = f"""

DIRECTIVES & TASK ORDER:
1. If water_available is False: Path to water tank at (75, 250) -> follow_path -> call collect_water().
2. Process crops sequentially in the exact order listed below:
   For each crop needing work: Path to (x, y) -> follow_path -> plant_crop(x, y) -> water().
3. Finish ONLY when all crops are planted and watered AND water_available is True.

CRITICAL RULES:
- THINKING LIMIT: Keep reasoning under 2 sentences. Focus ONLY on the immediate next action. Do NOT output multi-step plans or summaries.
- EXECUTION: Execute exactly 1 tool call per turn. Never output text descriptions of tool calls.


WORLD STATE:
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}

Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}

Water_available: {state["water_available"]}
Water_tank: {list(state['water_tank'])}

{tools_description}"""




system_message2 = f"""You are a smart farm game agent.

DIRECTIVES & TASK ORDER:
1. If water_available is False: Path to water tank at (75, 250) -> follow_path -> call collect_water().
2. Process crops sequentially in the exact order listed below:
   For each crop needing work: Path to (x, y) -> follow_path -> plant_crop(x, y) -> water().
3. Finish ONLY when all crops are planted and watered AND water_available is True.


WORLD STATE:
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}

Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}

Water_available: {state["water_available"]}
Water_tank: {list(state['water_tank'])}

{tools_description}"""

system_message3 = f"""You are a smart farm game agent.

DIRECTIVES & TASK ORDER:
1. If water_available is False: Path to water tank at (75, 250) -> follow_path -> call collect_water().
2. Process crops sequentially in the exact order listed below:
   For each crop needing work: Path to (x, y) -> follow_path -> plant_crop(x, y) -> water().
3. Finish ONLY when all crops are planted and watered AND water_available is True.

CRITICAL RULES:
- THINKING LIMIT: Keep reasoning under 2 sentences. Focus ONLY on the immediate next action. Do NOT output multi-step plans or summaries.
- EXECUTION: Execute exactly 1 tool call per turn. Never output text descriptions of tool calls.



{tools_description}"""


system_message4 = f"""You are a smart farm game agent.

DIRECTIVES & TASK ORDER:
1. If water_available is False: Path to water tank at (75, 250) -> follow_path -> call collect_water().
2. Process crops sequentially in the exact order listed below:
   For each crop needing work: Path to (x, y) -> follow_path -> plant_crop(x, y) -> water().
3. Finish ONLY when all crops are planted and watered AND water_available is True.

CRITICAL RULES:
- THINKING LIMIT: Keep reasoning under 2 sentences. Focus ONLY on the immediate next action. Do NOT output multi-step plans or summaries.
- EXECUTION: Execute exactly 1 tool call per turn. Never output text descriptions of tool calls.


WORLD STATE:
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}

Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}

Water_available: {state["water_available"]}
Water_tank: {list(state['water_tank'])}

"""




base_components = {
    "role": "You are a smart farm game agent.",
    "task": """
DIRECTIVES & TASK ORDER:
1. If water_available is False: Path to water tank at (75, 250) -> follow_path -> call collect_water().
2. Process crops sequentially in the exact order listed below:
   For each crop needing work: Path to (x, y) -> follow_path -> plant_crop(x, y) -> water().
3. Finish ONLY when all crops are planted and watered AND water_available is True.
""",

    "thinking_limit": """
    CRITICAL RULES:
    - THINKING LIMIT: Keep reasoning under 2 sentences.
    - Focus ONLY on the immediate next action.
    - Do NOT output multi-step plans or summaries.
    - EXECUTION: Execute exactly 1 tool call per turn.
    - Never output text descriptions of tool calls.
    """,

    "world_state": f"""
    WORLD STATE:
    Grid size: {state['grid_size']}
    Player position: {tuple(state['player_pos'])}

    Crops:
    {crops_to_text(state['crops'])}

    Obstacles:
    {list(state['obstacles'])}

    Water_available: {state["water_available"]}
    Water_tank: {list(state["water_tank"])}
    """,

    "tools": tools_description
}
full_prompt = "\n\n".join(base_components.values())

ablations = {
    "full": full_prompt,
    "no_role": "\n\n".join([
        base_components["task"],
        base_components["thinking_limit"],
        base_components["world_state"],
        base_components["tools"],
    ]),

    "no_thinking_limit": "\n\n".join([
        base_components["role"],
        base_components["task"],
        base_components["world_state"],
        base_components["tools"],
    ]),

    "no_world_state": "\n\n".join([
        base_components["role"],
        base_components["task"],
        base_components["thinking_limit"],
        base_components["tools"],
    ]),

    "no_tools_description": "\n\n".join([
        base_components["role"],
        base_components["task"],
        base_components["thinking_limit"],
        base_components["world_state"],
    ]),
}

