"""
Hardened version of agentic_approach2.py.

Why this exists: the original agentic_approach2.py prompt fails frequently with
gpt-oss:20b. The root causes observed in the logs (test_logs_astar/gpt-oss_20b.log)
were:

1. The loop hard-stops with "LLM did not call tools but goal is not complete."
   as soon as gpt-oss answers with text instead of a tool call. gpt-oss is a
   reasoning model that frequently emits a polite text summary ("Great! I've moved...",
   "Stop.") instead of the next move -> 0-point runs.
2. gpt-oss mis-formats astar arguments (strings instead of ints, single int
   instead of a list, etc.). The original astar error handler returns the
   useless string "pass correct argument to the tool." on which the agent loops.
3. The tool-result state sent back to the model used grid_size [5,5], a
   hardcoded obstacle [250,100], and only the crop the player is standing on.
   gpt-oss's own log calls this out ("grid_size [5,5], current_state has
   wrong format") and it loses track of the real world.
4. The system prompt says "Stop after each completed tool call and wait",
   which actively encourages gpt-oss to stop instead of continuing.
5. Context trimming at >10 messages discards the path mid-run, and there is
   no iteration cap for runaway reasoning loops.

Fixes implemented here:
- Never hard-stop on a text-only reply: nudge the model up to MAX_TEXT_RETRIES
  times to continue with a tool call, then stop cleanly.
- Hard iteration cap (MAX_ITERATIONS) so runaway loops are scored instead of hanging.
- astar is wrapped with argument validation/coercion while keeping the tool name
  "astar" (so the model calls it exactly as before).
- The model-facing state in every tool message is now accurate: full 800x600
  grid, all crops, water_tank and obstacles. The state posted to the game
  frontend keeps the original [5,5] format so the UI is unchanged.
- System prompt rewritten for gpt-oss robustness: explicit task order,
  explicit astar argument format, and a rule to NOT stop until done.
- Context trimming threshold raised (keep system + first user message + recent).

Interface is identical to the original: python agentic_approach2_fixed.py --model gpt-oss:20b
Logs still go to ../../experiments/test_logs_astar/<model>.log
"""

import requests
import time
import re
import matplotlib.pyplot as plt
import numpy as np
from a_star_algo import astar as _astar_impl
from ollama import Client
from ollama._types import ChatResponse
import json
import logging
import yaml, os, sys
import argparse
from speech_to_text import audio_text
logger = logging.getLogger(__name__)

def read_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)  # safe_load prevents code execution
            return config
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error reading file: {e}")
        sys.exit(1)

config_data = read_config("config.yaml")

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model",
    type=str,
    required=True,
    help="LLM model name"
)
args = parser.parse_args()
model = args.model
print(f"Running model: {model}")
# Use a separate folder for the fixed variant so A/B comparisons are clean
# (the original writes to test_logs_astar/gpt-oss_20b.log).
log_folder = "../../experiments/test_logs_astar_fixed"
os.makedirs(log_folder, exist_ok=True)

log_file_name = f"{model}"
f_log_file_name = log_file_name.replace(":", "_").replace(".", "_")
formatted_log_file_name = f"{f_log_file_name}.log"

log_file_folder_path = os.path.join(log_folder, formatted_log_file_name)

logging.basicConfig(filename=log_file_folder_path, encoding='utf-8', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True

logger.info("model_used_for_astar: " + model)
logger.info("agent_variant: fixed (agentic_approach2_fixed.py)")

url = config_data["server_urls"]["game_state_url"]

url2 = config_data["server_urls"]["whisper_url"]

new_content = ""
if config_data["speech"]["user_input"]:
    new_content = audio_text
else:
    st_time = time.time()
    with open("plant_crops_audio.m4a", "rb") as f:
        response = requests.post(url2, files={"file": f})

    print(response.json()["text"])

    print(time.time() - st_time)
    logger.info(f"time taken for api call + model: {time.time()-st_time}")
    print("time_take by model")
    model_time = response.json()["time_taken"]
    print(response.json()["time_taken"])
    logger.info(f"time taken for audio by model: {model_time}")

    new_content = response.json()["text"]

headers = {
    "Content-Type": "application/json"
}


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


invalid_moves = 0
revisits = 0
visited = set()
invalid_move_object = {}

def set_crop_state():
    """
    sets the water state of the crop
    """
    crops = state["crops"]
    is_goal_completed = False
    value = 0
    for crop in crops:
        if crops[crop[0], crop[1]]["needs_water"] == False:
            value += 1
    print("value of goal completed:" + str(value))
    if value == 2:
        state["goal_completed"] = True
    return state["goal_completed"]


def water() -> str:
    """
      waters the crop and changes the state accordingly.
      This tool is only used when the crop is planted and player is at the crops position.
      Args:
          None: No argument
      Returns:
        JSON string
         {
        "status":"true",
        "action":"water",
        "message": "status of the action"
       }
    """
    global invalid_moves, invalid_move_object
    pos = tuple(state["player_pos"])
    print(pos)
    crop = state["crops"].get(pos)
    print(crop)
    if not crop:
        invalid_moves += 1
        invalid_move_object["no crop"] = invalid_move_object.get("no crop", 0) + 1
        return json.dumps({
            "status": "false",
            "action": "water",
            "message": "no crop here"
        })
    if not crop["planted"]:
        invalid_moves += 1
        invalid_move_object["crop not planted"] = invalid_move_object.get("crop not planted", 0) + 1
        return json.dumps({
            "status": "false",
            "action": "water",
            "message": "crop not planted"
        })

    if not crop["needs_water"]:
        invalid_moves += 1
        invalid_move_object["crop already watered"] = invalid_move_object.get("crop already watered", 0) + 1
        return json.dumps({
            "status": "false",
            "action": "water",
            "message": "crop already watered"
        })

    crop["needs_water"] = False

    state["goal_completed"] = set_crop_state()
    return json.dumps({
        "status": "true",
        "action": "water",
        "message": "crop watered successfully"
    })


def collect_water() -> str:
    """
      collectes the water from the water container and changes the state of water_available accordingly
      This tool is only used when the player is at the water tanks position.
      Args:
          None: No argument
      Returns:
        JSON string
         {
        "status":"true",
        "action":"move",
        "message": "water tank status"
        "water_available": state["water_available"]
       }
    """
    global invalid_moves, invalid_move_object
    print(state["player_pos"][0])
    print(state["player_pos"][1])

    new_x = state["player_pos"][0]
    new_y = state["player_pos"][1]

    water_tank = (state["water_tank"])
    print(water_tank)
    if new_x != water_tank[0] or new_y != water_tank[1]:
        invalid_moves += 1
        invalid_move_object["no water tank here"] = invalid_move_object.get("no water tank here", 0) + 1
        return json.dumps({
            "status": "false",
            "action": "collect water",
            "message": "no water tank here",
            "water_available": state["water_available"]
        })

    state["water_available"] = True
    return json.dumps({
        "status": "true",
        "action": "collect water",
        "message": "water collected successfully",
        "water_available": state["water_available"]
    })


def crops_to_text(crops):
    lines = []
    for pos, info in crops.items():
        lines.append(f"- {pos}: needs_water = {info['needs_water']}")
    return "\n".join(lines)


def move(dx: int, dy: int) -> str:
    """
    Moves the game character by (dx, dy), updates the global state, and returns the updated state.

    Args:
        dx (int): x coordinate
        dy (int): y coordinate

    Returns:
    JSON string:
        {
            "status": true/false,
            "action": "plant_crop",
            "player_pos": [x, y],
            "error": optional string
        }
    """
    global invalid_moves, invalid_move_object, revisits

    new_x = state["player_pos"][0] + int(dx)
    new_y = state["player_pos"][1] + int(dy)

    # Bounds check
    if int(dx) > 0 and int(dy) > 0:
        invalid_moves += 1
        invalid_move_object["diagonal_move"] = invalid_move_object.get("diagonal_move", 0) + 1
        return json.dumps({
            "status": "false",
            "action": "move",
            "player_pos": state["player_pos"],
            "error": "diagonal move not allowed"
        })
    VALID_PAIRS = {(0, -25), (0, 25), (-25, 0), (25, 0)}
    if (dx, dy) not in VALID_PAIRS:
        invalid_moves += 1
        invalid_move_object["move tool argument values are not 25px"] = invalid_move_object.get("move tool argument values are not 25px", 0) + 1
        return json.dumps({
            "status": "false",
            "action": "move",
            "player_pos": state["player_pos"],
            "error": "invalid tool argument values check the rules again."
        })
    if not (0 <= new_x < state["grid_size"][0] and
            0 <= new_y < state["grid_size"][1]):
        invalid_moves += 1
        invalid_move_object["out of bounds"] = invalid_move_object.get("out of bounds", 0) + 1

        return json.dumps({
            "status": "false",
            "action": "move",
            "player_pos": state["player_pos"],
            "error": "Blocked: out of bounds"
        })

    # Obstacle check
    if (new_x, new_y) in state["obstacles"]:
        invalid_moves += 1
        invalid_move_object["blocked obstacle"] = invalid_move_object.get("blocked obstacle", 0) + 1
        return json.dumps({
            "status": "false",
            "action": "move",
            "player_pos": state["player_pos"],
            "error": "Blocked: obstacle"
        })
    if (new_x, new_y) in visited:
        revisits += 1
        state["player_pos"] = [new_x, new_y]
        return json.dumps({
            "status": "true",
            "action": "move",
            "player_pos": state["player_pos"]
        })
    else:
        visited.add((new_x, new_y))
        state["player_pos"] = [new_x, new_y]
        return json.dumps({
            "status": "true",
            "action": "move",
            "player_pos": state["player_pos"]
        })


def check_player_postion(crops, x, y, sx, sy):
    is_correct_position = False
    for k, v in crops.items():
        if (x == k[0] and y == k[1]) and (x == sx and y == sy):
            is_correct_position = True
    return is_correct_position


def plant_crop(x: int, y: int) -> str:
    """
    Plant a crop at the given grid coordinate (x,y).
    (x,y) are the player coordinates.
    This tool is only used when the player is at the crops position.
    Args:
        x (int): x coordinate
        y (int): y coordinate

    Returns:
        JSON string:
        {
            "status": true/false,
            "action": "plant_crop",
            "position": [x, y],
            "planted": true/false,
            "error": optional string
        }
    """
    global invalid_moves, invalid_move_object
    crop = state["crops"].get((x, y))

    new_x = state["player_pos"][0]
    new_y = state["player_pos"][1]

    is_correct_position = check_player_postion(state["crops"], new_x, new_y, x, y)

    if not is_correct_position:
        return json.dumps({
            "status": False,
            "error": "the player is not at the crop.",
            "position": [x, y]
        })

    if not crop:
        invalid_moves += 1
        invalid_move_object["No crop here"] = invalid_move_object.get("No crop here", 0) + 1
        return json.dumps({
            "status": False,
            "error": "No crop here",
            "position": [x, y]
        })

    if crop["planted"]:
        invalid_move_object["Already planted"] = invalid_move_object.get("Already planted", 0) + 1
        invalid_moves += 1
        return json.dumps({
            "status": False,
            "error": "Already planted",
            "position": [x, y]
        })

    crop["planted"] = True

    return json.dumps({
        "status": True,
        "action": "plant_crop",
        "position": [x, y],
        "planted": True
    })


# ---------------------------------------------------------------------------
# Hardened astar wrapper (keeps the tool name "astar" so the model calls it
# exactly as before, but validates/coerces the arguments so gpt-oss's format
# slips no longer produce the useless "pass correct argument to the tool."
# string).
# ---------------------------------------------------------------------------
_ASTAR_HINT = ("Required format: start_px=[x,y], goal_px=[x,y], "
               "obstacles_px=[[x1,y1],[x2,y2],...], grid_width=800, grid_height=600. "
               "Use integers, not strings.")


def astar(start_px=None, goal_px=None, obstacles_px=None, grid_width=800, grid_height=600) -> str:
    """
    A* pathfinding tool. Calculates a path from start_px to goal_px while
    avoiding the given obstacles. Do NOT include the goal in obstacles_px.

    Args:
        start_px (list[int, int]): x,y coordinates of the start position, e.g. [200, 100]
        goal_px (list[int, int]): x,y coordinate of the goal position, e.g. [75, 250]
        obstacles_px (list[list[int, int]]): list of obstacle coordinates, e.g. [[250, 100]]
        grid_width (int): grid width in pixels, use 800
        grid_height (int): grid height in pixels, use 600

    Returns:
        str: The path from the start to the destination as a list of pixel coordinates.
    """
    try:
        def to_pair(v, name):
            if v is None:
                raise ValueError(f"missing '{name}'")
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                return [int(v[0]), int(v[1])]
            if isinstance(v, str):
                nums = re.findall(r"-?\d+", v)
                if len(nums) >= 2:
                    return [int(nums[0]), int(nums[1])]
            raise ValueError(f"invalid '{name}': {v!r}")

        start = to_pair(start_px, "start_px")
        goal = to_pair(goal_px, "goal_px")

        obs = []
        if obstacles_px is not None:
            if isinstance(obstacles_px, dict):
                obstacles_px = list(obstacles_px.values())
            if not isinstance(obstacles_px, (list, tuple)):
                obstacles_px = [obstacles_px]
            for o in obstacles_px:
                obs.append(to_pair(o, "obstacles_px"))

        gw = int(grid_width) if str(grid_width).strip() else 800
        gh = int(grid_height) if str(grid_height).strip() else 600

        result = _astar_impl(tuple(start), tuple(goal), obs, grid_width=gw, grid_height=gh)
        if result is None:
            return json.dumps({"status": "false", "action": "astar", "message": "no path found"})
        return result
    except Exception as e:
        return json.dumps({"status": "false", "action": "astar", "message": f"{_ASTAR_HINT} Error: {e}"})


available_tools = {"move": move, "water": water, "astar": astar, "collect_water": collect_water, "plant_crop": plant_crop}

points_gained = 0
points_gained_object = {}

# ---------------------------------------------------------------------------
# Improved, explicit prompt. The original just dumped the python function
# dict ({move: <function move at 0x...>}) as "Tools available", which gives
# gpt-oss almost no information about argument formats. This version states
# the task order and every tool's exact signature.
# ---------------------------------------------------------------------------
tools_description = """
Tools available:
- move(dx: int, dy: int): Move the player exactly 25px in one axis.
  Valid argument pairs are ONLY: (0,-25), (0,25), (-25,0), (25,0).
  Diagonal moves or other distances are rejected.
- astar(start_px=[x,y], goal_px=[x,y], obstacles_px=[[x,y], ...], grid_width=800, grid_height=600):
  Returns the path from start_px to goal_px, avoiding obstacles_px.
  Pass integers, not strings. Do NOT include the goal in obstacles_px.
- collect_water(): Collect water at the water tank (75,250). Only works when
  the player is standing exactly on (75,250).
- plant_crop(x: int, y: int): Plant the crop at the player's current position.
- water(): Water the crop the player is currently standing on. Only succeeds
  when the crop is planted and water_available=True.
"""

system_message2 = f"""
you are smart farm game agent.

Rules
- Execute exactly one action per turn, and after each tool result IMMEDIATELY continue
  with the next tool call until the task is fully done. Never stop early and never
  just reply with text while the goal is still incomplete.
- Always use tools for movement, pathfinding, planting, watering and collecting water.
  Never describe a tool call as text, JSON, markdown or code -- call the tool directly.
- Movement: always use the move tool, exactly 25px in one axis at a time
  (valid pairs: (0,-25), (0,25), (-25,0), (25,0)). Never move diagonally.
- Always use the astar tool to obtain paths. Never calculate paths manually.

Task order (follow exactly):
1. Walk to the water tank at (75,250) and call collect_water().
2. Walk to the first crop, call plant_crop(x, y) while standing on it.
3. Call water() while standing on that crop.
4. Repeat for the other crop.
5. Only when EVERY crop is planted and watered and water_available=True, you may
   finish. Never output "stop" or a summary before that.

astar argument format (use integers, not strings):
    astar(start_px=[x,y], goal_px=[x,y], obstacles_px=[[x1,y1],[x2,y2],...], grid_width=800, grid_height=600)

WORLD STATE:

CURRENT STATE (authoritative):

Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}

Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}

Water_available:
{state["water_available"]}
Water_tank:
{list(state['water_tank'])}

the crops are not planted and not watered

move 25pxs and one side at a time

{tools_description}
"""

messages = [
    {'role': 'system', 'content': system_message2},
    {'role': 'user', 'content': new_content}
]

client = Client(
    host=config_data["server_urls"]["ollama_url"],
    timeout=60
)

time_taken = []
tool_calls_array = []
player_positions = []
total_output_tokens = 0
total_input_tokens = 0

# ---------------------------------------------------------------------------
# Hardened agent loop.
# ---------------------------------------------------------------------------
MAX_ITERATIONS = 80          # hard cap so runaway gpt-oss reasoning loops end cleanly
MAX_TEXT_RETRIES = 3          # how many text-only replies we tolerate before stopping
text_reply_streak = 0

try:
    new_crops = {}
    for iteration in range(MAX_ITERATIONS):
        # Context trimming: the original trimmed at >10 messages which dropped
        # the path/goal mid-run. Trim much later and keep the first two
        # messages (system + task) plus the recent history.
        if len(messages) > 30:
            messages = messages[:2] + messages[-24:]

        st_time = time.time()
        response: ChatResponse = client.chat(model=model, messages=messages, tools=[move, water, astar, collect_water, plant_crop])
        print(f"input_tokens: {response['prompt_eval_count']}")

        print("Prompt evaluation time:", response["prompt_eval_duration"] / 1e9, "seconds")
        logger.info(f"Prompt evaluation time:{response['prompt_eval_duration'] / 1e9:.2f}")

        print("Generation time:", response["eval_duration"] / 1e9, "seconds")
        logger.info(f"Generation time: {response['eval_duration'] / 1e9:.2f}")

        print(f"output_tokens: {response['eval_count']}")

        total_output_tokens += response['eval_count']
        total_input_tokens = response['prompt_eval_count']
        print(f"response time: {(response['total_duration']/1e9)}")
        logger.info(f"response time: {response['total_duration'] / 1e9:.2f}")

        if response.message.content:
            print('Content: ')
            print(response.message.content + '\n')
            logger.info(f"content : {response.message.content}")

        if response.message.thinking:
            print('Thinking: ')
            print(response.message.thinking + '\n')
            logger.info(f"thinking : {response.message.thinking}")

        messages.append(response.message)

        if response.message.tool_calls:
            text_reply_streak = 0
            for tool_call in response.message.tool_calls:
                # LLM decides which function to call
                function_to_call = available_tools.get(tool_call.function.name)
                real_result_json = ""
                if function_to_call:
                    try:
                        result = function_to_call(**tool_call.function.arguments)
                        print('Result from tool call name: ', tool_call.function.name, 'with arguments: ', tool_call.function.arguments, 'result: ', str(result) + '\n')
                        real_result_json = result
                    except Exception as e:
                        real_result_json = json.dumps({"status": "false", "message": f"Error in tool call: {str(e)}"})
                    logger.info(f"tool: {str(tool_call.function.name)}  result: {str(real_result_json)}")
                    print(f"tool: {str(tool_call.function.name)}  result: {str(real_result_json)}")
                    print(f"time for tool {tool_call.function.name}: {str(time.time()-st_time)}")
                    if "false" not in real_result_json:
                        tool_calls_array.append(tool_call.function.name)
                        time_taken.append(time.time() - st_time)

                    # Accurate model-facing state (fixes the old "grid_size [5,5],
                    # crops missing" problem that made gpt-oss lose track).
                    full_crops = {}
                    for j, (k, v) in enumerate(state["crops"].items(), start=1):
                        full_crops[f"crop{j}"] = {
                            "pos": list(k),
                            "name": v["name"],
                            "needs_water": v["needs_water"],
                            "planted": v["planted"],
                        }
                    model_state = {
                        "grid_size": [800, 600],
                        "player_pos": list(state["player_pos"]),
                        "crops": full_crops,
                        "obstacles": list(state["obstacles"]),
                        "water_available": state["water_available"],
                        "water_tank": list(state["water_tank"]),
                        "goal_completed": state["goal_completed"],
                    }

                    # Frontend state: keep the exact original format so the game
                    # UI / server contract is unchanged.
                    j = 0
                    new_crops = {}
                    for k, v in state["crops"].items():
                        j += 1
                        if state["player_pos"] == list(k):
                            new_crops[f"crop{j}"] = {
                                "pos": list(k),
                                "name": state["crops"][tuple(state["player_pos"])]["name"],
                                "needs_water": state["crops"][tuple(state["player_pos"])]["needs_water"],
                                "planted": state["crops"][tuple(state["player_pos"])]["planted"],
                            }
                    new_state = {
                        "grid_size": [5, 5],
                        "player_pos": state["player_pos"],
                        "crops": new_crops,
                        "obstacles": [250, 100],
                        "water_available": state["water_available"],
                        "goal_completed": state["goal_completed"],
                    }

                    messages.append({
                        "role": "tool",
                        "content": json.dumps({
                            "action_result": result,
                            "current_state": model_state
                        }),
                        "tool_name": tool_call.function.name
                    })

                    print("new_state")
                    print(new_state)
                    player_positions.append(state["player_pos"])
                    new_state["task"] = new_content
                    new_task_state = new_state
                    response = requests.post(url, json=new_task_state, headers=headers)
                    print(response)
                else:
                    print(f'Tool {tool_call.function.name} not found')
                    messages.append({'role': 'tool', 'content': f'Tool {tool_call.function.name} not found', 'tool_name': tool_call.function.name})

            if state["goal_completed"]:
                print("goal completed")
                break
            continue

        # No tool calls were made this turn.
        if state["goal_completed"]:
            print("goal completed")
            break

        # gpt-oss (and other reasoning models) sometimes answer with text only.
        # Instead of hard-stopping like the original, nudge it to keep going.
        text_reply_streak += 1
        print(f"LLM did not call tools but goal is not complete. (text streak = {text_reply_streak})")
        logger.info(f"LLM did not call tools but goal is not complete. (text streak = {text_reply_streak})")
        if text_reply_streak >= MAX_TEXT_RETRIES:
            logger.info("LLM did not call tools after repeated nudges; stopping run.")
            print("LLM did not call tools after repeated nudges; stopping run.")
            break
        messages.append({
            "role": "user",
            "content": ("You answered with text but did not call a tool. "
                        "Continue the task now: make the next tool call "
                        "(astar, move, collect_water, plant_crop, or water) using the tool interface.")
        })
except Exception as e:
    logger.error(f"LLm failed due to error: {str(e)}")
    print(f"LLm failed due to error: {str(e)}")

if state["water_available"] == True:
    points_gained += 1
    points_gained_object["water_available"] = 1

reset_crop = {}
j = 0
crops = state["crops"]
for k, v in crops.items():
    j += 1
    reset_crop[f"crop{j}"] = {"pos": list(k), "name": crops.get(k)["name"], "needs_water": True, "planted": False}
    if crops.get(k)["planted"] == True:
        points_gained_object[f"plant_crop_{j}"] = 1
        points_gained += 1
    if crops.get(k)["needs_water"] == False:
        points_gained_object[f"needs_water_{j}"] = 1
        points_gained += 1

reset_state = {
    "grid_size": [5, 5],
    "player_pos": [200, 100],
    "crops": reset_crop,
    "obstacles": [250, 100],
    "water_available": False,
    "goal_completed": state["goal_completed"]
}

response = requests.post(url, json=reset_state, headers=headers)

print(time_taken)
if len(time_taken) > 0 and len(tool_calls_array) > 0:
    data = time_taken
    mean = np.mean(data)
    median = np.median(data)
    variance = np.var(data)
    std_dev = np.std(data)
    min_val = np.min(data)
    max_val = np.max(data)

    stats = {
        "mean": mean,
        "median": median,
        "variance": variance,
        "std_dev": std_dev,
        "min": min_val,
        "max": max_val
    }

    normalized = (data - min_val) / (max_val - min_val)
    z_scores = (data - mean) / std_dev

    print("No of llms calls:-")
    print(len(time_taken))
    logger.info(f"No of llms calls: {len(time_taken)}")

    print("total time taken:")
    print(np.sum(time_taken))

    print("tool calls:")
    print(tool_calls_array)

    print("player positons:")
    print(player_positions)
    logger.info(f"player_positions: {player_positions}")

    print(f"points gained by agent: {str(points_gained)}")
    logger.info(f"points gained by agent: {str(points_gained)}")
    print(f"points gained object: {str(points_gained_object)}")
    logger.info(f"points gained object: {str(points_gained_object)}")

    plt.plot(time_taken)
    logger.info(f"time taken values: {time_taken}")
    print("total input tokens: " + str(total_input_tokens))
    print("total output tokens: " + str(total_output_tokens))
    logger.info("total input tokens: " + str(total_input_tokens))
    logger.info("total output tokens: " + str(total_output_tokens))
else:
    print(f"points gained by agent: {str(points_gained)}")
    logger.info(f"points gained by agent: {str(points_gained)}")
    logger.info("llm tool failed")
    print("llm tool failed")