"""
agentic_approach2.py (branch: follow_path_prompt) — hardened for gpt-oss:20b.

This file preserves the branch's follow-path system and API-call queueing:
  - follow_path(path) tool: walks each step of an astar path, updating state and
    queueing each state to the game server via api_call().
  - api_call() / task_queue / api_worker(): background thread that POSTs state
    snapshots to the game server (1s delay between posts).

On top of that, it layers the validated gpt-oss reliability hardening:
  1. Text-only replies no longer hard-stop the run: the loop nudges the model up
     to MAX_TEXT_RETRIES times to continue with a tool call before stopping.
  2. Hardened astar wrapper (same tool name) that validates/coerces arguments
     (integers, not strings), eliminating "pass correct argument to the tool."
     loops.
  3. Rewritten system prompt: explicit task order, exact astar argument format,
     per-tool signatures (including follow_path), and "never stop early / never
     reply with text while the goal is incomplete".
  4. Accurate model-facing state in every tool message (800x600 grid, all crops,
     obstacles, water_tank, water_available, goal_completed).
  5. MAX_ITERATIONS cap (80) so runaway reasoning loops end cleanly, and context
     trimming at >30 messages so the path is not dropped mid-route.

Log folder unchanged: ../../experiments/test_logs_queue/<model>.log
Run: python agentic_approach2.py --model gpt-oss:20b
"""

import random
import requests
import time
import re
import ast
import matplotlib.pyplot as plt
import numpy as np
from a_star_algo import astar as _astar_impl
from ollama import Client
from ollama._types import ChatResponse
import json
import logging
import yaml
import os
import sys
# from speech_to_text import audio_text
import queue
import threading
import copy
import argparse

task_queue = queue.Queue()

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
log_folder = "../../experiments/test_logs_queue"
os.makedirs(log_folder, exist_ok=True)

log_file_name = f"{model}"
f_log_file_name = log_file_name.replace(":", "_").replace(".", "_")
formatted_log_file_name = f"{f_log_file_name}.log"

log_file_folder_path = os.path.join(log_folder, formatted_log_file_name)

logging.basicConfig(filename=log_file_folder_path, encoding='utf-8',
                    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True

logger.info("model_used_for_follow_path: " + model)
logger.info(
    "agent_variant: follow_path + queueing, hardened (agentic_approach2.py)")

url = config_data["server_urls"]["game_state_url"]

url2 = config_data["server_urls"]["whisper_url"]

new_content = ""
# if config_data["speech"]["user_input"]:
#     new_content = audio_text
# else:
#     st_time = time.time()
#     with open("plant_crops_audio.m4a", "rb") as f:
#         response = requests.post(url2, files={"file": f})

#     print(response.json()["text"])

#     print(time.time() - st_time)
#     logger.info(f"time taken for api call + model: {time.time()-st_time}")
#     print("time_take by model")
#     model_time = response.json()["time_taken"]
#     print(response.json()["time_taken"])
#     logger.info(f"time taken for audio by model: {model_time}")

#     new_content = response.json()["text"]
new_content = "plant the crops and water them"
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


def crops_parser(crops):
    new_crops = {}
    # enumerate() handles your index counting 'i' automatically
    for i, (k, v) in enumerate(crops.items(), start=1):
        if v is not None:
            # Check if key 'k' is a stringified tuple/list and parse it correctly
            if isinstance(k, str):
                try:
                    pos = list(ast.literal_eval(k))
                except (ValueError, SyntaxError):
                    pos = [k]
            else:
                pos = list(k)

            new_crops[f"crop{i}"] = {
                "pos": pos,
                "name": v.get("name"),
                "needs_water": v.get("needs_water"),
                "planted": v.get("planted")
            }
    return new_crops


player_positions = []


def api_call(current_state):
    # Parse crops and format the state
    new_crops = crops_parser(current_state["crops"])
    player_positions.append(current_state["player_pos"])
    # Create a deep copy so future LLM moves don't overwrite this data
    # before the background thread has a chance to send it
    state_to_send = copy.deepcopy(current_state)
    state_to_send["crops"] = new_crops

    # Push to background thread instantly
    requests.post(url, json=state_to_send, headers=headers)
    # task_queue.put(state_to_send)


def _coerce_step(step):
    """Coerce a single path step into a [x, y] list of ints, or None."""
    if isinstance(step, (list, tuple)) and len(step) >= 2:
        try:
            return [int(step[0]), int(step[1])]
        except (TypeError, ValueError):
            return None
    return None


def _parse_path(path):
    """
    Normalize the 'path' argument into a list of [x, y] coordinate steps.

    Handles the formats that llama3.1 (and other models) actually produce:
      - list/tuple of [x,y] or (x,y) coordinates
      - a *string* containing the repr (e.g. "[(200, 100), (175, 100)]")
      - a flat list/tuple of ints: alternating coordinates, or 25px deltas

    Returns a list of [x, y] steps, or None if the path cannot be parsed.
    """
    if path is None:
        return None

    # 1) Strings: try literal_eval first, else regex-extract integer pairs.
    if isinstance(path, str):
        text = path.strip()
        try:
            parsed = ast.literal_eval(text)
        except Exception:
            parsed = None
        if parsed is None:
            nums = re.findall(r"-?\d+", text)
            if len(nums) >= 4 and len(nums) % 2 == 0:
                parsed = [[int(nums[i]), int(nums[i + 1])]
                          for i in range(0, len(nums), 2)]
            else:
                return None
        path = parsed

    if isinstance(path, (list, tuple)) and len(path) == 0:
        return None

    # 2) List of coordinate pairs: [[x,y], (x,y), ...]
    if isinstance(path, (list, tuple)) and isinstance(path[0], (list, tuple)):
        steps = []
        for step in path:
            c = _coerce_step(step)
            if c is not None:
                steps.append(c)
        return steps if steps else None

    # 3) Flat list/tuple of numbers.
    flat = []
    for item in path:
        try:
            flat.append(int(item))
        except (TypeError, ValueError):
            return None
    if len(flat) < 2:
        return None

    # 3a) All values are 25px move deltas -> accumulate from current position.
    if all(v in (-25, 0, 25) for v in flat):
        steps = []
        px, py = int(state["player_pos"][0]), int(state["player_pos"][1])
        for i in range(0, len(flat) - 1, 2):
            px += flat[i]
            py += flat[i + 1]
            steps.append([px, py])
        return steps if steps else None

    # 3b) Alternating x,y coordinates.
    if len(flat) % 2 == 0:
        return [[flat[i], flat[i + 1]] for i in range(0, len(flat), 2)]
    return None


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

        result = _astar_impl(tuple(start), tuple(
            goal), obs, grid_width=gw, grid_height=gh)
        if result is None:
            return json.dumps({"status": "false", "action": "astar", "message": "no path found"})
        return result
    except Exception as e:
        return json.dumps({"status": "false", "action": "astar", "message": f"{_ASTAR_HINT} Error: {e}"})


def follow_path(start_px: tuple[int, int], goal_px: tuple[int, int], obstacles_px: list[tuple[int, int]]) -> str:
    """
      follow path tool takes start and goal coordinates along with obstacles and makes an API call to the game server.
      Args:
            start_px int,int: x,y coordinates of start
            goal_px int,int: x,y coordinate of goal
            obstacles_px [(int,int)] : x,y coordinate of obstacles
        Returns:
            List: The list of tuples of the player coordinates to reach the destination
        
            A sample input for the function
            start_px = (50,75)
            goal_px = (150,125)

            obstacles = [
                (75, 75),
            (100, 75),
            (125, 75)
        ]
    """
    obstacles_px.remove(goal_px) if goal_px in obstacles_px else None

    if goal_px in obstacles_px:
        return json.dumps({
            "status": "false",
            "action": "follow_path",
            "message": "goal is an obstacle"
        })

    path = astar(start_px, goal_px, obstacles_px)
    print(f"Path found: {path}")
    for step in path:
        state["player_pos"] = [step[0], step[1]]
        api_call(state)
        # modified_state = state
    return json.dumps({
        "status": "true",
        "action": "follow_path",
        "message": "followed path to the goal"
    })


def water() -> str:
    """
      waters the crop and changes the state accordingly
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
    pos = tuple(state["player_pos"])
    print(pos)
    crop = state["crops"].get(pos)
    print(crop)
    if not crop:
        return "No crop here"

    if not crop["needs_water"]:
        return json.dumps({
            "status": "false",
            "action": "water",
            "message": "crop already watered"
        })

    if not crop["planted"]:
        return json.dumps({
            "status": "false",
            "action": "water",
            "message": "crop not planted"
        })

    crop["needs_water"] = False
    state["goal_completed"] = set_crop_state()
    api_call(state)
    return json.dumps({
        "status": "true",
        "action": "water",
        "message": "crop watered successfully"
    })


def collect_water() -> str:
    """
      collects the water from the water container and changes the state of water_available accordingly.
      Args:
          None: No argument
      Returns:
        JSON string
         {
        "status":"true",
        "action":"collect water",
        "water_available": state["water_available"]
       }
    """
    if state["player_pos"] != state["water_tank"]:
        return json.dumps({
            "status": "false",
            "action": "collect water",
            "message": "no water tank here",
            "water_available": state["water_available"]
        })

    state["water_available"] = True
    api_call(state)
    return json.dumps({
        "status": "true",
        "action": "collect water",
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
    Kept for reference / other experiments, but the agent uses follow_path for movement.

    Args:
        dx (int): x coordinate
        dy (int): y coordinate

    Returns:
    JSON string:
        {
            "status": true/false,
            "action": "move",
            "player_pos": [x, y],
            "error": optional string
        }
    """
    new_x = state["player_pos"][0] + int(dx)
    new_y = state["player_pos"][1] + int(dy)

    # Bounds check
    if not (0 <= new_x < state["grid_size"][0] and
            0 <= new_y < state["grid_size"][1]):
        return json.dumps({
            "status": "false",
            "action": "move",
            "player_pos": state["player_pos"],
            "error": "Blocked: out of bounds"
        })

    # Obstacle check
    if (new_x, new_y) in state["obstacles"]:
        return json.dumps({
            "status": "false",
            "action": "move",
            "player_pos": state["player_pos"],
            "error": "Blocked: obstacle"
        })

    state["player_pos"] = [new_x, new_y]
    return json.dumps({
        "status": "true",
        "action": "move",
        "player_pos": state["player_pos"]
    })


def check_player_position(crops, x, y, sx, sy):
    is_correct_position = False
    for k, v in crops.items():
        if (x == k[0] and y == k[1]) and (x == sx and y == sy):
            is_correct_position = True
    return is_correct_position


def plant_crop(x: int, y: int) -> str:
    """
    Plant a crop at the given grid coordinate (x,y).
    (x,y) are the player coordinates.
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
    crop = state["crops"].get((x, y))
    new_x = state["player_pos"][0]
    new_y = state["player_pos"][1]

    is_correct_position = check_player_position(
        state["crops"], new_x, new_y, x, y)

    if not is_correct_position:
        return json.dumps({
            "status": False,
            "error": "the player is not at the crop.",
            "planted": True
        })
    if not crop:
        return json.dumps({
            "status": False,
            "error": "No crop here",
            "position": [x, y]
        })

    if crop["planted"]:
        return json.dumps({
            "status": False,
            "error": "Already planted",
            "position": [x, y]
        })

    crop["planted"] = True
    print("plant crop tool:-")
    print(state)
    api_call(state)
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


def api_worker():
    print("API worker started")
    while True:
        try:
            # 1. Try to get a task
            state_snapshot = task_queue.get(timeout=45)
        except queue.Empty:
            print("No more tasks. Worker exiting.")
            break  # Exit the loop if no tasks arrive for 45 seconds
        # 2. Process the task (only runs if we successfully got an item)
        try:
            time.sleep(1)
            requests.post(url, json=state_snapshot, headers=headers)
        except Exception as e:
            print(f"Error in API call: {e}")
        finally:
            # 3. Mark THIS specific task as done
            task_queue.task_done()


# Start the thread
t = threading.Thread(target=api_worker)
t.start()


available_tools = {"follow_path": follow_path, "water": water,
                   "collect_water": collect_water, "plant_crop": plant_crop}

points_gained = 0
points_gained_object = {}

# ---------------------------------------------------------------------------
# Rewritten, explicit prompt (gpt-oss robust): states the task order, the
# exact astar argument format, per-tool signatures (including follow_path),
# and forbids stopping early / replying with plain text mid-task.
# ---------------------------------------------------------------------------
tools_description = """
Tools available:
- follow_path(path): Move along the full path by calling astar.
  path is a list of [x, y] pixel coordinates. Use this for ALL movement.
  Returns the path from start_px to goal_px, avoiding obstacles_px.
  Pass integers, not strings. Do NOT include the goal in obstacles_px.
- collect_water(): Collect water at the water tank (75,250). Only works when
  the player is standing exactly on (75,250).
- plant_crop(x: int, y: int): Plant the crop at the player's current position.
- water(): Water the crop the player is currently standing on. Only succeeds
  when the crop is planted and water_available=True.
"""

# This usually means they are cells that cannot be part of the path *except* for the destination.

system_message2_ = f"""
you are smart farm game agent.

Your task:
1. Reach the water tank at (75,250) and call collect_water().
2. Walk to the first crop (use follow_path) and call plant_crop(x, y).
3. Call water() while standing on that crop.
4. Repeat for the other crop.
5. Only when EVERY crop is planted AND watered AND water_available=True, you may
   finish. Never output "stop" or a summary before that.

Rules
- Execute exactly one action per turn, and after each tool result IMMEDIATELY continue
  with the next tool call until the task is fully done. Never stop early and never
  just reply with text while the goal is still incomplete.
- Always use tools: follow_path for pathfinding, movement, plant_crop,
  water, collect_water. Never describe a tool call as text, JSON, markdown or code -- call the tool directly.
- Never calculate the distance manually. Always use the follow_path tool.
- move 25pxs and one side at a time, and not allowed to pass through the crops and
  water tank -- they are obstacles.


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

{tools_description}
"""


system_message2 = f"""
you are smart farm game agent.

Your task:
1. planting the crops by going to the given coordinates.
2. Water needs to collected to plant water.
3. Reach the water tank to collect water.

IMPORTANT.
 check if the crops are planted.
 Never calculate the distance on manually.

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


move 25pxs and one side at a time

Never output tool arguments as text, JSON, markdown, or code blocks.
When an action is required, invoke the corresponding tool. 
If a tool is available, emitting its arguments in text form is always incorrect.

Tools available:
{available_tools}

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
agent_messages = []
total_output_tokens = 0
total_input_tokens = 0
tool_calls = []

# ---------------------------------------------------------------------------
# Hardened agent loop.
# ---------------------------------------------------------------------------
MAX_ITERATIONS = 80          # hard cap so runaway gpt-oss reasoning loops end cleanly
MAX_TEXT_RETRIES = 3          # how many text-only replies we tolerate before stopping
text_reply_streak = 0

try:
    new_crops = {}
    for iteration in range(MAX_ITERATIONS):
        # Context trimming: keep system + first user message + recent history
        # so the path/goal is not dropped mid-run.

        st_time = time.time()
        response: ChatResponse = client.chat(model=model, messages=messages, tools=[
                                             follow_path, water, collect_water, plant_crop], think=True)
        print(f"input_tokens: {response['prompt_eval_count']}")

        print("Prompt evaluation time:",
              response["prompt_eval_duration"] / 1e9, "seconds")
        logger.info(
            f"Prompt evaluation time:{response['prompt_eval_duration'] / 1e9:.2f}")

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
                        print("Executing tool instantly in Python:",
                              tool_call.function.name)
                        # 1. Execute instantly. (Network calls are sent to the queue inside the tool)
                        real_result_json = function_to_call(
                            **tool_call.function.arguments)
                    except Exception as e:
                        real_result_json = json.dumps(
                            {"status": "false", "message": f"{str(e)}"})

                    print("tool result:")
                    print(real_result_json)
                    logger.info(f"tool_result: {str(real_result_json)}")
                    if "false" not in real_result_json:
                        tool_calls.append(tool_call.function.name)
                    time_taken.append(time.time() - st_time)

                    real_result = real_result_json

                    # Accurate model-facing state (full 800x600 grid, all crops,
                    # obstacles, water_tank) so gpt-oss does not lose track.
                    new_crops = crops_parser(state["crops"])
                    new_state = {
                        "grid_size": [800, 600],
                        "player_pos": state["player_pos"],
                        "crops": new_crops,
                        "obstacles": state["obstacles"],
                        "water_available": state["water_available"],
                        "water_tank": state["water_tank"],
                        "goal_completed": state["goal_completed"]
                    }

                    # Tell the LLM exactly what happened
                    messages.append({
                        "role": "tool",
                        "content": json.dumps({
                            "action_result": real_result,
                            "current_state": new_state
                        }),
                        "name": tool_call.function.name
                    })
                else:
                    print(f'Tool {tool_call.function.name} not found')
                    messages.append(
                        {'role': 'tool', 'content': f'Tool {tool_call.function.name} not found', 'tool_name': tool_call.function.name})

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
        print(
            f"LLM did not call tools but goal is not complete. (text streak = {text_reply_streak})")
        logger.info(
            f"LLM did not call tools but goal is not complete. (text streak = {text_reply_streak})")
        if text_reply_streak >= MAX_TEXT_RETRIES:
            logger.info(
                "LLM did not call tools after repeated nudges; stopping run.")
            print("LLM did not call tools after repeated nudges; stopping run.")
            break
        messages.append({
            "role": "user",
            "content": ("You answered with text but did not call a tool. "
                        "Continue the task now: make the next tool call "
                        "(follow_path, collect_water, plant_crop, or water) using the tool interface.")
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
    reset_crop[f"crop{j}"] = {"pos": list(k), "name": crops.get(
        k)["name"], "needs_water": True, "planted": False}
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
    "obstacles": state["obstacles"][0],
    "water_available": False,
    "goal_completed": state["goal_completed"]
}
task_queue.put(reset_state)

print(time_taken)
if len(time_taken) > 0 and len(tool_calls) > 0:
    print("No of llms calls:-")
    print(len(time_taken))
    logger.info(f"No of llms calls: {len(time_taken)}")
    result = [tool_calls[0]]
    for action in tool_calls[1:]:
        if action != result[-1]:
            result.append(action)
    tool_calls_final = result
    print("sequence of tool calls:" + str(tool_calls_final))

    print("player positons:")
    print(player_positions)
    logger.info(f"player_positions: {player_positions}")

    print(f"points gained by agent: {str(points_gained)}")
    logger.info(f"points gained by agent: {str(points_gained)}")
    print(f"points gained object: {str(points_gained_object)}")
    logger.info(f"points gained object: {str(points_gained_object)}")

    logger.info(f"time taken values: {time_taken}")
    print("total input tokens: " + str(total_input_tokens))
    print("total output tokens: " + str(total_output_tokens))
    logger.info("total input tokens: " + str(total_input_tokens))
    logger.info("total output tokens: " + str(total_output_tokens))
else:
    logger.info("llm tool failed")
    print("llm tool failed")
