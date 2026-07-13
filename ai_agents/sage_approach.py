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
import argparse
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
log_folder = "../../experiments/test_logs_sage"
os.makedirs(log_folder, exist_ok=True)

# log_file_name = config_data["log_file"]["name"]
log_file_name = f"baseline_{model}"
f_log_file_name = log_file_name.replace(":","_").replace(".","_")
formatted_log_file_name = f"{f_log_file_name}.log"

log_file_folder_path = os.path.join(log_folder, formatted_log_file_name)
logging.basicConfig(filename=log_file_folder_path, encoding='utf-8', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
    "player_pos": [200, 100], 
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
        invalid_move_object["No crop here."] = invalid_move_object.get("No crop here", 0) + 1
        return json.dumps({"status": "false", "message": "wrong position to plant crop", "position": [x, y]})

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
points_gained = 0
points_gained_object = {}

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
client = Client(host=config_data["server_urls"]["ollama_url"], timeout=60)
model = config_data["model"]["name"]

reasoning_model = config_data["reasoning_model"]["name"]
messages = [
    {'role':'system','content':system_message2},
    {'role': 'user', 'content': new_content}
]

def consolidate_memory(client, model, memory_data, threshold=5):
    """
    Checks if memory exceeds the threshold. If so, uses the LLM to merge 
    duplicate or overlapping lessons into generalized rules.
    """
    lessons = memory_data.get("lessons", [])
    
    if len(lessons) <= threshold:
        return memory_data

    logger.info("Memory threshold reached. Consolidating lessons...")
    print("\n[SAGE] Consolidating and pruning redundant memories...")

    # We provide explicit environment constraints so the LLM doesn't invent fake rules
    prune_prompt = f"""
    You are a memory optimizer for an AI farming agent. 
    Below is a list of lessons the agent has learned from failing. Merge duplicate or overlapping lessons into single, generalized rules.
    
    CRITICAL GAME ENGINE RULES (Do not contradict these):
    - The 'move' tool requires exactly 25px steps relative displacements. Valid pairs are only (0, -25), (0, 25), (-25, 0), or (25, 0).
    - Diagonal moves are strictly forbidden.
    - Absolute coordinates cannot be passed to the 'move' tool.
    
    Current Lessons to Consolidate:
    {json.dumps(lessons, indent=2)}
    
    Your task:
    1. Merge duplicates into generalized, accurate rules.
    2. Keep the rules concise and actionable.
    
    Respond ONLY with a valid JSON array of strings representing the new consolidated rules.
    Example output format:
    [
        "Rule 1 text here",
        "Rule 2 text here"
    ]
    """

    try:
        response = client.chat(
            model=model, 
            messages=[{"role": "user", "content": prune_prompt}],
            format="json" 
        )
        
        raw_output = json.loads(response.message.content)
        consolidated_lessons = []
        
        # Flexibly handle if the LLM returns a list directly, OR wraps it in a dict
        if isinstance(raw_output, list):
            consolidated_lessons = raw_output
        elif isinstance(raw_output, dict):
            # Grab the first list found in the dictionary keys (like 'rules' or 'lessons')
            for key, val in raw_output.items():
                if isinstance(val, list):
                    consolidated_lessons = val
                    break

        if consolidated_lessons:
            print(f"[SAGE] Successfully reduced {len(lessons)} lessons to {len(consolidated_lessons)} generalized rules.")
            memory_data["lessons"] = consolidated_lessons
            return memory_data
        else:
            logger.error(f"LLM output could not be parsed into a clean list. Raw: {raw_output}")
            return memory_data

    except Exception as e:
        logger.error(f"Failed to consolidate memory due to error: {e}")
        return memory_data


time_taken = []
player_positions = []
log_messages = []
total_output_tokens = 0
total_input_tokens = 0
tool_calls = []
new_crops = {}
llm_mistakes = 0
try:
    new_crops = {}
    i = 0
    while i < 70:
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
                    is_failure = False
                    error_reason = ""
                    result_dict = {}

                    # ==================================================
                    # LOCALIZED TOOL CALL EXECUTION (Safeguard Against TypeErrors)
                    # ==================================================
                    try:
                        result = function_to_call(**tool_call.function.arguments)
                        result_dict = json.loads(result)
                        
                        # Check for logical validation failures
                        if result_dict.get("status") in ["false", False]:
                            is_failure = True
                            error_reason = result_dict.get("message", "Logical rule violation")

                    except TypeError as e:
                        # This catches the model passing bad arguments like 'x' to water()
                        is_failure = True
                        error_reason = f"Invalid Tool Arguments! TypeError: {str(e)}"
                        result_dict = {"status": "false", "message": error_reason}
                        
                    except Exception as e:
                        # Catches any other unexpected runtime exceptions
                        is_failure = True
                        error_reason = f"Execution Error: {str(e)}"
                        result_dict = {"status": "false", "message": error_reason}

                    # Track analytics
                    log_messages.append({'role': 'tool', 'content': json.dumps(result_dict), 'tool_name': tool_call.function.name})
                    tool_calls.append(tool_call.function.name)
                    time_taken.append(time.time() - st_time)
                    player_positions.append(state["player_pos"])
                    print("tool call name:")
                    print(tool_call.function.name)
                    print("tool call arguments:")
                    print(tool_call.function.arguments)
                    # ==========================================
                    # SAGE: Reflection Generation on Failure
                    # ==========================================
                    if result_dict.get("status") in ["false", False] or is_failure:
                        llm_mistakes +=1
                        logger.info(f"Failure detected ({error_reason}). Triggering SAGE Reflection.")
                        print(f"\n[SAGE] Learning from error: {error_reason}")
                        
                        reflection_prompt = (
                            f"You attempted the action '{tool_call.function.name}' with arguments {tool_call.function.arguments}, "
                            f"but it failed with this error: '{error_reason}'. "
                            "Write a concise, 1-sentence rule so you don't make this exact mistake again in the future."
                        )
                        
                        reflection_resp = client.chat(model=reasoning_model, messages=[{"role": "user", "content": reflection_prompt}])
                        lesson = reflection_resp.message.content.strip()
                        
                        # Store in long term memory
                        sage_memory["lessons"].append(lesson)

                        sage_memory = consolidate_memory(client, model, sage_memory, threshold=5)
                        save_memory(sage_memory)
                        
                        # Inject directly into short term memory (current episode context)
                        messages.append({
                            'role': 'system', 
                            'content': f"[SYSTEM REFLECTION OVERRIDE]: Based on your last failure, remember this rule: {lesson}"
                        })
                    # ==========================================

                    # State update formatting for server
                    crops = state["crops"]
                    p = 0
                    for k,v in crops.items():   
                      p+=1
                      if crops.get(k) != None:
                        if state["player_pos"] == list(k):
                          new_crops[f"crop{p}"] = {"pos":list(k),"name":crops.get(tuple(state["player_pos"]))["name"],"needs_water":crops.get(tuple(state["player_pos"]))["needs_water"],"planted":crops.get(tuple(state["player_pos"]))["planted"]}
                
                    new_state = {
                        "grid_size": [5, 5],
                        "player_pos": state["player_pos"],
                        "crops": new_crops,
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
            print("goal_completed")
            break
        elif llm_mistakes == 10:
            logger.error(f"llm mistakes limit reached")
            print("llm mistakes limit reached")
            break

        elif response.message.tool_calls == None:
            messages.append({'role': 'user', 'content': "You did not select a tool. Please review your plan and select the next tool to execute."})
            if len(messages) > 150: 
                logger.error(f"Message limit reached, aborting to prevent infinite loop.")
                break
except Exception as e:
    print(f"llm failed due to error: {e}")
    logger.error(f"LLm failed due to error: {str(e)}")

# Remaining script logic (scoring, stats formatting, etc) goes here...
if state["water_available"] == True:
    points_gained +=1
    points_gained_object["water_available"] = 1

reset_crop = {}
j = 0
crops = state["crops"]
for k,v in crops.items():
    j+=1    
    reset_crop[f"crop{j}"] = {"pos":list(k),"name":crops.get(k)["name"],"needs_water":True,"planted":False}
    if crops.get(k)["planted"] == True:
        points_gained_object[f"plant_crop_{j}"] = 1
        points_gained+=1
    if crops.get(k)["needs_water"] == False:
        points_gained_object[f"needs_water_{j}"] = 1
        points_gained+=1


reset_state = {
            "grid_size": [5, 5],
            "player_pos": [200,100],

            "crops": reset_crop,
            # {
            #     "crop1":{"pos":[400,275],"name":"wheat","needs_water":True,"planted":False},
            #     "crop2":{"pos":[300,200],"name":"rice","needs_water":True,"planted":False},
            #     # "crop3":{"pos":[200,475],"needs_water":True,"planted":False},
            #     # "crop4":{"pos":[150,300],"needs_water":True,"planted":False},
            #     # "crop5":{"pos":[275,325],"needs_water":True,"planted":False}
            # },
            "obstacles": [250,100],
            "water_available":False,
            "goal_completed": state["goal_completed"]
        }

response = requests.post(url, json=reset_state, headers=headers)






def check_sequence_details(actual, correct):
    matched_elements = []
    
    for i, action in enumerate(actual):
        # Case 1: Actual sequence is longer than the correct sequence
        if i >= len(correct):
            print(f"Result: WRONG")
            print(f" -> Matched until: {matched_elements}")
            print(f" -> Reason: 'actual' sequence is longer than 'correct' sequence.")
            return False, matched_elements
        
        # Case 2: Element matches
        if action == correct[i]:
            matched_elements.append(action)
        else:
            # Case 3: Element does not match
            print(f"Result: WRONG")
            print(f" -> Matched until: {matched_elements}")
            print(f" -> At position {i}, expected '{correct[i]}' but got '{action}'")
            return False, matched_elements
            
    # If it finishes the loop, it's a perfect prefix match
    print(f"Result: CORRECT")
    print(f" -> Matched until: {matched_elements}")
    return True, matched_elements



correct_seq = ['move', 'collect_water', 'move', 'plant_crop','water', 'move', 'plant_crop','water']

# print("--- Test sequence ---")
# actual_1 = tool_calls
# check_sequence_details(actual_1, correct_seq)


print(time_taken)
if len(time_taken)>0:
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


    print("player positons:")
    print(player_positions)
    logger.info(f"player_positions: {player_positions}")

    print(f"points gained by agent: {str(points_gained)}")
    logger.info(f"points gained by agent: {str(points_gained)}")
    print(f"points gained object: {str(points_gained_object)}")
    logger.info(f"points gained object: {str(points_gained_object)}")

    plt.plot(time_taken)
    logger.info(f"time taken values: {time_taken}")
    print("total input tokens: "+str(total_input_tokens))
    print("total output tokens: "+str(total_output_tokens))
    logger.info("total input tokens: "+str(total_input_tokens))
    logger.info("total output tokens: "+str(total_output_tokens))
    
    result = [tool_calls[0]]
    for action in tool_calls[1:]:
        if action != result[-1]:
            result.append(action)
    tool_calls_final = result
    print("--- Test sequence ---")
    actual_1 = tool_calls_final
    check_sequence_details(actual_1, correct_seq)
    print("sequence of tool calls:"+ str(tool_calls_final))
    logger.info("sequence of tool calls:"+ str(tool_calls_final))
    threshold = 25
    points = player_positions

    jumps = 0
    for i in range(len(points) - 1):
        
        x1, y1 = points[i]
        x2, y2 = points[i + 1]

        if abs(x2 - x1) > threshold or abs(y2 - y1) > threshold:
            jumps +=1
            print(f"Jump > {threshold}px: {points[i]} -> {points[i+1]}")
    print("game character jumps:"+ str(jumps))
    logger.info("game character jumps:"+ str(jumps))
    invalid_moves+=jumps
    invalid_move_rate = invalid_moves / len(player_positions)
    print("invalid move rate:")
    print(invalid_move_rate)
    print("no of invalid moves:"+ str(invalid_moves))
    print("invalid move object:")
    print(invalid_move_object)
    logger.info("no of invalid moves:"+ str(invalid_moves))
    logger.info("game character jumps:"+ str(jumps))
    print("no of revisits:")
    print(str(revisits))
    logger.info("no of revisits:"+ str(revisits))
    crossed_obstacle = 0
    for play_pos in player_positions:
        if play_pos == state["obstacles"][0]:
            crossed_obstacle+=1
        if play_pos == state["water_tank"]:
            crossed_obstacle+=1
    print("crossed_obstacles:")
    print(crossed_obstacle)

else:
    logger.info(log_messages)
    logger.info("llm tool failed") 
    print("llm tool failed")
