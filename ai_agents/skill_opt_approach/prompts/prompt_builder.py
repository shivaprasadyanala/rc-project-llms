from pathlib import Path
state = {
    "grid_size": (800, 600),

    # Player
    "player_pos": [300, 100],  # use list for mutability

    # Crops indexed by position
    "crops": {
        (400, 275): {"name":"wheat","planted":False,"needs_water": True},
        (300, 200): {"name":"rice","planted":False,"needs_water": True},
        # (200,475): {"name":"sugarcane","planted":False,"needs_water": True},
        # (150,300): {"planted":False,"needs_water": True},
        # (275,325): {"planted":False,"needs_water": True}
    },

    # Obstacles as a set for fast lookup
    "obstacles": [[250, 100]],
    "water_available":False,
    "water_tank":[75,250],

    # Goal tracking
    "goal_completed": False
}

PROMPT_DIR = Path("prompts")


def load_system_prompt():
    return (PROMPT_DIR / "system_prompt.txt").read_text()


def load_skill():
    return (PROMPT_DIR / "best_skill.md").read_text()


def crops_to_text(crops):
    lines = []
    for pos, info in crops.items():
      lines.append(f"- {pos}: needs_water = {info['needs_water']}")
    return "\n".join(lines)


def build_world_state(state):

    return f"""
    CURRENT STATE

    Grid size:
    {state['grid_size']}

    Player position:
    {tuple(state['player_pos'])}

    Water Available:
    {state['water_available']}

    Water Tank:
    {list(state['water_tank'])}

    Obstacles:
    {list(state['obstacles'])}

    Crops:
    {crops_to_text(state['crops'])}
    """


def build_prompt(state, available_tools):

    system = load_system_prompt()

    skill = load_skill()

    world = build_world_state(state)

    return f"""
{system}

==========================
CURRENT SKILL
==========================

{skill}

==========================
WORLD STATE
==========================

{world}

==========================
TOOLS
==========================

{available_tools}
"""