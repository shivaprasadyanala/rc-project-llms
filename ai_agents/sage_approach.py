import random
import requests
import time
import matplotlib.pyplot as plt
import numpy as np
from ollama import Client
from ollama._types import ChatResponse
import json
import logging
import yaml, os, sys
from speech_to_text import audio_text

logger = logging.getLogger(__name__)

def read_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            return config
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error reading file: {e}")
        sys.exit(1)

config_data = read_config("config.yaml")

log_file_name = config_data["log_file"]["name"]
logging.basicConfig(filename=log_file_name, encoding='utf-8', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True

logger.info("model_used_for_baseline: "+ config_data["model"]["name"])

url = config_data["server_urls"]["game_state_url"]
url2 = config_data["server_urls"]["whisper_url"]

new_content = ""
if config_data["speech"]["user_input"]:
    new_content = audio_text
else:
    st_time = time.time()
    with open("plant_crops_audio.m4a", "rb") as f:
        response = requests.post(url2, files={"file": f})

    model_time = response.json()["time_taken"]
    logger.info(f"time taken for audio by model: {model_time}")
    new_content = response.json()["text"]

headers = {"Content-Type": "application/json"}

state = {
    "grid_size": (800, 600),
    "player_pos": [300, 100], 
    "crops": {
        (400, 275): {"name":"wheat","planted":False,"needs_water": True},
        (300, 200): {"name":"rice","planted":False,"needs_water": True},
    },
    "obstacles": [[250, 100]],
    "water_available":False,
    "water_tank":[75,250],
    "goal_completed": False
}

invalid_moves = 0
revisits = 0
visited = set()
invalid_move_object = {}

# ==========================================
# SAGE: Memory Management System
# ==========================================
MEMORY_FILE = "sage_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {"lessons": []}

def save_memory(memory_data):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory_data, f, indent=4)

sage_memory = load_memory()
# ==========================================

def set_crop_state():
    crops = state["crops"]
    value = 0
    for crop in crops:
      if crops[crop[0],crop[1]]["planted"] == True and crops[crop[0],crop[1]]["needs_water"] == False:
        value+=1
    if value == 2:
        state["goal_completed"]= True
    return state["goal_completed"]

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
    global invalid_moves, invalid_move_object
    pos = tuple(state["player_pos"])
    crop = state["crops"].get(pos)
    
    if not crop:
        invalid_moves += 1
        invalid_move_object["no crop"] = invalid_move_object.get("no crop", 0) + 1
        return json.dumps({"status":"false", "action":"water", "message": "no crop here"})
    if not crop["planted"]:
        invalid_moves += 1
        invalid_move_object["crop not planted"] = invalid_move_object.get("crop not planted", 0) + 1
        return json.dumps({"status":"false", "action":"water", "message": "crop not planted"})
    if not crop["needs_water"]:
        invalid_moves += 1
        invalid_move_object["crop already watered"] = invalid_move_object.get("crop already watered", 0) + 1
        return json.dumps({"status":"false", "action":"water", "message": "crop already watered"})

    crop["needs_water"] = False
    state["goal_completed"] = set_crop_state()
    return json.dumps({"status":"true", "action":"water", "message": "crop watered successfully"})

def collect_water() -> str:
    """
      collectes the water from the water container and changes the state of water_available accordingly
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
    new_x, new_y = state["player_pos"][0], state["player_pos"][1]
    water_tank = state["water_tank"]
    
    if new_x != water_tank[0] or new_y != water_tank[1]:
        invalid_moves +=1
        invalid_move_object["no water tank here"] = invalid_move_object.get("no water tank here", 0) + 1
        return json.dumps({"status":"false", "action":"collect water", "message":"no water tank here", "water_available": state["water_available"]})

    state["water_available"] = True
    return json.dumps({"status":"true", "action":"collect water", "message":"water collected successfully", "water_available": state["water_available"]})

def crops_to_text(crops):
    lines = []
    for pos, info in crops.items():
      lines.append(f"- {pos}: needs_water = {info['needs_water']}")
    return "\n".join(lines)

def move(dx:int, dy:int) -> str:
    """
    Moves the game character by (dx, dy), updates the global state, and returns the updated state.

    Args:
        dx (int): x coordinate
        dy (int): ý coordinate

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

    if int(dx) > 0 and int(dy) > 0:
        invalid_moves += 1
        invalid_move_object["diagonal_move"] = invalid_move_object.get("diagonal_move", 0) + 1
        return json.dumps({"status":"false", "action":"move", "player_pos": state["player_pos"], "message":"diagonal move not allowed"})
    
    VALID_PAIRS = {(0, -25), (0, 25), (-25, 0),(25, 0)}
    if (dx,dy) not in VALID_PAIRS:
        invalid_moves+=1
        invalid_move_object["move tool argument values are not 25px"] = invalid_move_object.get("move tool argument values are not 25px", 0) + 1
        return json.dumps({"status":"false", "action":"move", "player_pos": state["player_pos"], "message":"invalid tool argument values check the rules again."})
    
    if not (0 <= new_x < state["grid_size"][0] and 0 <= new_y < state["grid_size"][1]):
        invalid_moves+=1
        invalid_move_object["out of bounds"] = invalid_move_object.get("out of bounds", 0) + 1
        return json.dumps({"status":"false", "action":"move", "player_pos": state["player_pos"], "message":"Blocked: out of bounds"})

    if (new_x, new_y) in state["obstacles"]:
        invalid_moves+=1
        invalid_move_object["blocked obstacle"] = invalid_move_object.get("blocked obstacle", 0) + 1
        return json.dumps({"status":"false", "action":"move", "player_pos": state["player_pos"], "message":"Blocked: obstacle"})
    
    if (new_x, new_y) in visited:
        revisits+=1
        
    visited.add((new_x, new_y))
    state["player_pos"] = [new_x, new_y]
    return json.dumps({"status":"true", "action":"move", "player_pos": state["player_pos"]})

def plant_crop(x:int, y:int) -> str:
    """
    Plant a crop at the given grid coordinate (x,y).
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

    if not crop:
        invalid_moves+=1
        invalid_move_object["No crop here"] = invalid_move_object.get("No crop here", 0) + 1
        return json.dumps({"status": "false", "message": "No crop here", "position": [x, y]})

    if crop["planted"]:
        invalid_move_object["Already planted"] = invalid_move_object.get("Already planted", 0) + 1
        invalid_moves+=1
        return json.dumps({"status": "false", "message": "Already planted", "position": [x, y]})

    crop["planted"] = True
    return json.dumps({"status": "true", "action": "plant_crop", "position": [x, y], "planted": True})

available_tools = {"move":move, "water":water, "collect_water":collect_water, "plant_crop":plant_crop}

# ==========================================
# SAGE: Inject Long-Term Memory into System Prompt
# ==========================================
lessons_text = "\n".join([f"- {lesson}" for lesson in sage_memory["lessons"]])
if not lessons_text:
    lessons_text = "None yet."

system_message2 = f"""
you are smart farm game agent.

Your task:
1. planting the crops by going to the given coordinates.
2. Water needs to collected to plant water.
3. Reach the water tank to collect water.

IMPORTANT. check if the crops are planted.

PAST LESSONS (DO NOT REPEAT THESE MISTAKES):
{lessons_text}

WORLD STATE:
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}
Crops:
{crops_to_text(state['crops'])}
Obstacles: {list(state['obstacles'])}
Water_available: {state["water_available"]}
Water_tank: {list(state['water_tank'])}

Move 25pxs and one side at a time. Not allowed to pass through crops or water tanks.
Call only one tool at a time.
Never output tool arguments as text, JSON, markdown, or code blocks.
"""

messages = [
    {'role':'system','content':system_message2},
    {'role': 'user', 'content': new_content}
]

client = Client(host=config_data["server_urls"]["ollama_url"], timeout=60)
model = config_data["model"]["name"]

time_taken = []
player_positions = []
log_messages = []
total_output_tokens = 0
total_input_tokens = 0
tool_calls = []
new_crops = {}

try:
    new_crops = {}
    i = 0
    while i < 50:
        i += 1
        st_time = time.time()    
        
        response: ChatResponse = client.chat(model=model, messages=messages, tools=[move,water,collect_water,plant_crop])

        total_output_tokens += response['eval_count']
        total_input_tokens = response['prompt_eval_count']
        
        if response.message.content:
            log_messages.append(response.message.content)
        if response.message.thinking:
            log_messages.append(response.message.thinking)

        messages.append(response.message)
        
        if response.message.tool_calls:
            for tool_call in response.message.tool_calls:
                function_to_call = available_tools.get(tool_call.function.name)
                
                if function_to_call:
                    result = function_to_call(**tool_call.function.arguments)
                    result_dict = json.loads(result)
                    
                    log_messages.append({'role': 'tool', 'content': result, 'tool_name': tool_call.function.name})
                    tool_calls.append(tool_call.function.name)
                    time_taken.append(time.time()-st_time)
                    player_positions.append(state["player_pos"])
                    print("tool call name:")
                    print(tool_call.function.name)
                    # ==========================================
                    # SAGE: Reflection Generation on Failure
                    # ==========================================
                    if result_dict.get("status") in ["false", False]:
                        logger.info("Failure detected. Triggering SAGE Reflection.")
                        error_reason = result_dict.get("message", "Unknown error")
                        
                        reflection_prompt = (
                            f"You attempted the action '{tool_call.function.name}' with arguments {tool_call.function.arguments}, "
                            f"but it failed with this error: '{error_reason}'. "
                            "Write a concise, 1-sentence rule so you don't make this exact mistake again in the future."
                        )
                        
                        reflection_resp = client.chat(model=model, messages=[{"role": "user", "content": reflection_prompt}])
                        lesson = reflection_resp.message.content.strip()
                        
                        # Store in long term memory
                        sage_memory["lessons"].append(lesson)
                        save_memory(sage_memory)
                        
                        # Inject directly into short term memory (current episode context)
                        messages.append({
                            'role': 'system', 
                            'content': f"[SYSTEM REFLECTION OVERRIDE]: Based on your last failure, remember this rule: {lesson}"
                        })
                    # ==========================================

                    # State update formatting for server
                    # p = 0
                    # for k,v in crops.items():   
                    #   p+=1
                    #   if crops.get(k) != None:
                    #     if state["player_pos"] == list(k):
                    #       new_crops[f"crop{p}"] = {"pos":list(k),"name":crops.get(tuple(state["player_pos"]))["name"],"needs_water":crops.get(tuple(state["player_pos"]))["needs_water"],"planted":crops.get(tuple(state["player_pos"]))["planted"]}
                
                    new_state = {
                        "grid_size": [5, 5],
                        "player_pos": state["player_pos"],
                        # "crops": new_crops,
                        "obstacles": [250,100],
                        "water_available":state["water_available"],
                        "goal_completed": state["goal_completed"]
                    }
                    print("new state")
                    print(new_state)
                    
                    messages.append({
                        "role": "tool",
                        "content": json.dumps({
                            "action_result": result_dict,
                            "current_state": new_state
                        }),
                        "tool_name": tool_call.function.name
                    })

                    new_state["task"] = new_content
                    requests.post(url, json=new_state, headers=headers)
                else:
                    messages.append({'role': 'tool', 'content': f'Tool {tool_call.function.name} not found', 'tool_name': tool_call.function.name})
                    
        elif state["goal_completed"]:
            break
        elif response.message.tool_calls == None:
            messages.append({'role': 'user', 'content': "You did not select a tool. Please review your plan and select the next tool to execute."})
            if len(messages) > 50: 
                logger.error(f"Message limit reached, aborting to prevent infinite loop.")
                break
except Exception as e:
    logger.error(f"LLm failed due to error: {str(e)}")

# Remaining script logic (scoring, stats formatting, etc) goes here...