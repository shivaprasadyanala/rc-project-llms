import time
import requests
import matplotlib.pyplot as plt
import numpy as np
import json
import logging
import yaml
import os
import sys
import dspy
from a_star_algo import astar
from speech_to_text import audio_text

# ---------------------------------------------------------
# 1. Configuration & Setup
# ---------------------------------------------------------
logger = logging.getLogger(__name__)

def read_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading config: {e}")
        sys.exit(1)

config_data = read_config("config.yaml")

logging.basicConfig(
    filename=config_data["log_file"]["name"], 
    encoding='utf-8', 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True

game_server_url = config_data["server_urls"]["game_state_url"]
headers = {"Content-Type": "application/json"}

# Determine User Intent
new_content = ""
if config_data["speech"]["user_input"]:
    new_content = audio_text
else:
    # Audio fallback processing
    whisper_url = config_data["server_urls"]["whisper_url"]
    st_time = time.time()
    with open("plant_crops_audio.m4a", "rb") as f:
        response = requests.post(whisper_url, files={"file": f})
    
    audio_data = response.json()
    new_content = audio_data["text"]
    logger.info(f"Time taken for api call + model: {time.time()-st_time}")
    logger.info(f"Time taken for audio by model: {audio_data['time_taken']}")

# ---------------------------------------------------------
# 2. Game State & Tracking
# ---------------------------------------------------------
state = {
    "grid_size": (800, 600),
    "player_pos": [200, 100], 
    "crops": {
        (400, 275): {"name":"wheat","planted":False,"needs_water": True},
        (300, 200): {"name":"rice","planted":False,"needs_water": True},
        (200, 475): {"name":"sugarcane","planted":False,"needs_water": True},
    },
    "obstacles": {(250, 100)},
    "water_available": False,
    "water_tank": {(75, 250)},
    "goal_completed": False
}

# Metrics to track equivalent to your original loop
time_taken = []
player_positions = []
points_gained = 0
points_gained_object = {}

def set_crop_state():
    crops = state["crops"]
    value = sum(1 for pos, info in crops.items() if not info["needs_water"])
    if value == 3:
        state["goal_completed"] = True
    return state["goal_completed"]

def format_state_for_server(action_result):
    """Helper to convert the global state into the format the server expects"""
    new_crops = {}
    i = 1
    for k, v in state["crops"].items():
        if state["player_pos"] == list(k):
            new_crops[f"crop{i}"] = {
                "pos": list(k),
                "name": v["name"],
                "needs_water": v["needs_water"],
                "planted": v["planted"]
            }
        i += 1

    return {
        "grid_size": [5, 5], # Maintaining your hardcoded override from original code
        "player_pos": state["player_pos"],
        "crops": new_crops,
        "obstacles": [250, 100],
        "water_available": state["water_available"],
        "goal_completed": state["goal_completed"],
        "task": new_content
    }

def post_to_server(action_result):
    """Handles the side-effect of posting to the server after a tool executes."""
    try:
        new_task_state = format_state_for_server(action_result)
        response = requests.post(game_server_url, json=new_task_state, headers=headers)
        player_positions.append(state["player_pos"])
        logger.info(f"Server updated. Response: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to post to server: {e}")

# ---------------------------------------------------------
# 3. DSPy Tools (Refactored)
# ---------------------------------------------------------
# Note: In DSPy, docstrings are crucial. We also embed the time tracking
# and server POSTing directly into the tools so DSPy's automated loop handles it.

def water() -> str:
    """Waters the crop at the current position."""
    st_time = time.time()
    pos = tuple(state["player_pos"])
    crop = state["crops"].get(pos)

    if not crop:
        result = json.dumps({"status": "false", "action": "water", "message": "No crop here"})
    elif not crop["needs_water"]:
        result = json.dumps({"status": "false", "action": "water", "message": "crop already watered"})
    else:
        crop["needs_water"] = False
        state["goal_completed"] = set_crop_state()
        result = json.dumps({"status": "true", "action": "water", "message": "crop watered successfully"})

    time_taken.append(time.time() - st_time)
    post_to_server(result)
    return result

def collect_water() -> str:
    """Collects water from the water container."""
    st_time = time.time()
    state["water_available"] = True
    result = json.dumps({"status": "true", "action": "collect water", "water_available": state["water_available"]})
    
    time_taken.append(time.time() - st_time)
    post_to_server(result)
    return result

def move(dx: int, dy: int) -> str:
    """Moves the game character by (dx, dy). Must be 25px at a time. Move one axis at a time."""
    st_time = time.time()
    new_x = state["player_pos"][0] + int(dx)
    new_y = state["player_pos"][1] + int(dy)

    if not (0 <= new_x < state["grid_size"][0] and 0 <= new_y < state["grid_size"][1]):
        result = json.dumps({"status": "false", "action": "move", "error": "Blocked: out of bounds"})
    elif (new_x, new_y) in state["obstacles"]:
        result = json.dumps({"status": "false", "action": "move", "error": "Blocked: obstacle"})
    else:
        state["player_pos"] = [new_x, new_y]
        result = json.dumps({"status": "true", "action": "move", "player_pos": state["player_pos"]})

    time_taken.append(time.time() - st_time)
    post_to_server(result)
    return result

def plant_crop(x: int, y: int) -> str:
    """Plants a crop at the given grid coordinate (x,y)."""
    st_time = time.time()
    crop = state["crops"].get((x, y))

    if not crop:
        result = json.dumps({"status": False, "error": "No crop here", "position": [x, y]})
    elif crop["planted"]:
        result = json.dumps({"status": False, "error": "Already planted", "position": [x, y]})
    else:
        crop["planted"] = True
        result = json.dumps({"status": True, "action": "plant_crop", "position": [x, y], "planted": True})

    time_taken.append(time.time() - st_time)
    post_to_server(result)
    return result

# ---------------------------------------------------------
# 4. DSPy Agent Setup
# ---------------------------------------------------------
def format_world_state():
    crops_text = "\n".join([f"- {pos}: needs_water = {info['needs_water']}" for pos, info in state['crops'].items()])
    return f"""
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}
Crops:
{crops_text}
Obstacles: {list(state['obstacles'])}
Water_available: {state["water_available"]}
Water_tank: {list(state['water_tank'])}
"""

class FarmAgentSignature(dspy.Signature):
    """
    You are a smart farm game agent.
    
    Your task:
    1. Plant the crops by going to the given coordinates.
    2. Water needs to be collected to water crops.
    3. Reach the water tank to collect water.

    IMPORTANT RULES:
    - Check if the crops are planted.
    - Move 25pxs and one side at a time.
    - Do not pass through crops (crops are not obstacles).
    - STRICT: You must output exactly the JSON keys requested. Do not invent new keys like "next_multiple_of_tool_name". Use exactly "next_tool_name".
    """
    world_state: str = dspy.InputField(desc="Current authoritative game state")
    user_instruction: str = dspy.InputField(desc="User command via text or audio")
    next_action: str = dspy.OutputField(desc="Concluding thought or action state once goal is met")

# Initialize LLM
lm = dspy.LM(
    model="ollama/gemma4:26b", 
    api_base=config_data["server_urls"]["ollama_url"],
    max_tokens=1000,
    temperature=0.0
)
dspy.settings.configure(lm=lm)

# Initialize ReAct Agent
agent = dspy.ReAct(
    FarmAgentSignature, 
    tools=[move, water, collect_water, plant_crop], # Add astar back here if implemented
    max_iters=20 # Set a safe upper bound to prevent infinite loops
)

# ---------------------------------------------------------
# 5. Execution & Scoring
# ---------------------------------------------------------
print("Starting DSPy Agent Loop...")
try:
    # This single call replaces your entire `while True` loop
    result = agent(
        world_state=format_world_state(),
        user_instruction=new_content
    )
    print("\nAgent Finished. Final thoughts:", result.next_action)
except Exception as e:
    logger.error(f"LLm failed due to error: {str(e)}")
    print(f"Agent failed: {e}")

# Calculate points
if state["water_available"]:
    points_gained += 1
    points_gained_object["water_available"] = 1

j = 0
reset_crop = {}
for k, v in state["crops"].items():
    j += 1    
    reset_crop[f"crop{j}"] = {"pos": list(k), "name": v["name"], "needs_water": True, "planted": False}
    if v["planted"]:
        points_gained_object[f"plant_crop_{j}"] = 1
        points_gained += 1
    if not v["needs_water"]:
        points_gained_object[f"needs_water_{j}"] = 1
        points_gained += 1

# Reset State POST
reset_state = {
    "grid_size": [5, 5],
    "player_pos": [200, 100],
    "crops": reset_crop,
    "obstacles": [250, 100],
    "water_available": False,
    "goal_completed": state["goal_completed"]
}
requests.post(game_server_url, json=reset_state, headers=headers)

# Print & Log Stats
if len(time_taken) > 0:
    data = time_taken
    stats = {
        "mean": np.mean(data),
        "median": np.median(data),
        "variance": np.var(data),
        "std_dev": np.std(data),
        "min": np.min(data),
        "max": np.max(data)
    }

    print(f"No of tool calls: {len(time_taken)}")
    logger.info(f"No of tool calls: {len(time_taken)}")
    print(f"Player positons: {player_positions}")
    print(f"Points gained by agent: {points_gained}")
    print(f"Points gained object: {points_gained_object}")
    logger.info(f"Points gained object: {points_gained_object}")

    plt.plot(time_taken)
    plt.xlabel('Tool call run')
    plt.ylabel('Time (s)')
    plt.title('Processing time for each tool call')
    plt.show()
else:
    logger.info("LLM tool failed to execute properly.")
    print("LLM tool failed.")

# To inspect the exact prompt trajectory & tokens used:
print("\n--- DSPy LLM History ---")
lm.inspect_history(n=1)