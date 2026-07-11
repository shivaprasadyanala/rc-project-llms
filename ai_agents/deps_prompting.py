
import random
import requests
import time
import matplotlib.pyplot as plt
import numpy as np
from ollama import Client
from ollama._types import ChatResponse
import json
import logging
import yaml,os,sys
from speech_to_text import audio_text
import argparse
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
log_folder = "../../experiments/test_logs_baseline"
os.makedirs(log_folder, exist_ok=True)

# log_file_name = config_data["log_file"]["name"]
log_file_name = f"baseline_{model}"
f_log_file_name = log_file_name.replace(":","_").replace(".","_")
formatted_log_file_name = f"{f_log_file_name}.log"

log_file_folder_path = os.path.join(log_folder, formatted_log_file_name)

logging.basicConfig(filename=log_file_folder_path, encoding='utf-8', level=logging.INFO,format="%(asctime)s - %(levelname)s - %(message)s")
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

    print(response.json()["text"])

    print(time.time()-st_time)
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
        (400, 275): {"name":"wheat","planted":False,"needs_water": True},
        (300, 200): {"name":"rice","planted":False,"needs_water": True},
        # (200,475): {"name":"sugarcane","planted":False,"needs_water": True},
        # (150,300): {"planted":False,"needs_water": True},
        # (275,325): {"planted":False,"needs_water": True}
    },

    # Obstacles as a set for fast lookup
    "obstacles": {(250, 100)},
    "water_available":False,
    "water_tank":{(75,250)},

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
      if crops[crop[0],crop[1]]["needs_water"] == False and crops[crop[0],crop[1]]["needs_water"] == False:
        value+=1
    print("value of goal completed:" + str(value))
    if value ==2:
        state["goal_completed"]= True
    return state["goal_completed"]


# set_crop_state()
# breakpoint()
def water()-> str:
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
    global invalid_moves,invalid_move_object
    pos = tuple(state["player_pos"])
    print(pos)
    crop = state["crops"].get(pos)
    print(crop)
    if not crop:
        invalid_moves+=1
        invalid_move_object["no crop"] +=1
        return {
        "status":"false",
        "action":"water",
        "message": "no crop here"
        }
    if not crop["planted"]:
        invalid_moves+=1
        invalid_move_object["crop not planted"] +=1
        return {
        "status":"false",
        "action":"water",
        "message": "crop not planted"
        }

    if not crop["needs_water"]:
        invalid_moves+=1
        # return "Crop already watered"
        invalid_move_object["crop already watered"] +=1
        return {
        "status":"false",
        "action":"water",
        "message": "crop already watered"
        }

    crop["needs_water"] = False

    state["goal_completed"] = set_crop_state()
    # return "Crop watered successfully"
    return json.dumps({
        "status":"true",
        "action":"water",
        "message": "crop watered successfully"
        })
# water()
# breakpoint()

def collect_water()-> str:
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
    global invalid_moves,invalid_move_object
    print(state["player_pos"][0])
    print(state["player_pos"][1])

    new_x = state["player_pos"][0]
    new_y = state["player_pos"][1]

    water_tank = list(state["water_tank"])[0]
    if new_x != water_tank[0] or new_y != water_tank[1]:
        invalid_moves +=1
        invalid_move_object["no water tank here"] +=1
        {
        "status":"false",
        "action":"collect water",
        "message":"no water tank here",
        "water_available": state["water_available"]
        }

    # water_tank_y = state["water_tank"][1]
    state["water_available"] = True
    # print("in collect water tool.............")
    return json.dumps({
        "status":"true",
        "action":"collect water",
        "message":"water collected successfully",
        "water_available": state["water_available"]
    })


def crops_to_text(crops):
    lines = []
    for pos, info in crops.items():
      lines.append(f"- {pos}: needs_water = {info['needs_water']}")
    return "\n".join(lines)

def move(dx:int, dy:int)-> str:
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
    global invalid_moves,invalid_move_object,revisits

    new_x = state["player_pos"][0] + int(dx)
    new_y = state["player_pos"][1] + int(dy)

    # Bounds check
    if int(dx) > 0 and int(dy) > 0:
        invalid_moves+=1
        invalid_move_object["diagonal_move"] = invalid_move_object.get("diagonal_move", 0) + 1
        return json.dumps({
        "status":"false",
        "action":"move",
        "player_pos": state["player_pos"],
        "error":"diagonal move not allowed"
        })

    VALID_PAIRS = {(0, -25), (0, 25), (-25, 0),(25, 0)}
    if (dx,dy) not in VALID_PAIRS:
        invalid_moves+=1
        invalid_move_object["move tool argument values are not 25px"] = invalid_move_object.get("move tool argument values are not 25px", 0) + 1
        return json.dumps({
        "status":"false",
        "action":"move",
        "player_pos": state["player_pos"],
        "error":"invalid tool argument values check the rules again."
        })

    if not (0 <= new_x < state["grid_size"][0] and
            0 <= new_y < state["grid_size"][1]):
        invalid_moves+=1
        invalid_move_object["out of bounds"] +=1
        return json.dumps({
        "status":"false",
        "action":"move",
        "player_pos": state["player_pos"],
        "error":"Blocked: out of bounds"
        })

    # Obstacle check
    if (new_x, new_y) in state["obstacles"]:
        invalid_moves+=1
        invalid_move_object["blocked obstacle"] +=1
        return json.dumps({
        "status":"false",
        "action":"move",
        "player_pos": state["player_pos"],
        "error":"Blocked: obstacle"
        })
    if (new_x, new_y) in visited:
        revisits+=1
        state["player_pos"] = [new_x, new_y]
        return json.dumps({
            "status":"true",
            "action":"move",
            "player_pos": state["player_pos"]
        })
    else:
        visited.add((new_x, new_y))
        state["player_pos"] = [new_x, new_y]
        # return f"game character moved to {(new_x, new_y)}"
        return json.dumps({
            "status":"true",
            "action":"move",
            "player_pos": state["player_pos"]
        })


def plant_crop(x:int, y:int)-> str:
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
    global invalid_moves,invalid_move_object
    crop = state["crops"].get((x, y))

    if not crop:
        invalid_moves+=1
        invalid_move_object["No crop here"] +=1
        return json.dumps({
            "status": False,
            "error": "No crop here",
            "position": [x, y]
        })

    if crop["planted"]:
        invalid_move_object["Already planted"] +=1
        invalid_moves+=1
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
# tool_call = response.message.tool_calls[0]

#     result = function_to_call(**tool_call.function.arguments)

#     messages.append({
#         "role": "tool",
#         "content": json.dumps({
#             "tool": tool_call.function.name,
#             "result": result,
#             "state": state
#         })
#     })

#     continue

available_tools = {"move":move,"water":water,"collect_water":collect_water,"plant_crop":plant_crop}

points_gained = 0
points_gained_object = {}


# - You can ONLY move a maximum of 25px per step (dx, dy must be <= 25 or >= -25).
# - Do not pass through obstacles.
# - Crops are not obstacles.

# - Movement is strictly ORTHOGONAL (one side at a time).
# - You can ONLY move exactly 25px per step. 
# - Diagonal movement is STRICTLY FORBIDDEN. If dx is non-zero, dy MUST be 0. If dy is non-zero, dx MUST be 0.
# - Therefore, your ONLY valid move inputs are: (25, 0), (-25, 0), (0, 25), or (0, -25).
# - Do not pass through obstacles.
# - Crops are not obstacles.

# INSTRUCTIONS (Plan & Select):
# Before selecting a tool, you MUST output your reasoning using these exact headers:

# **Describe:** [Briefly state your current coordinates and the status of the crops/water].
# **Explain:** [Explain what you need to do next, or explain why your last move failed].
# **Plan:** [List your step-by-step orthogonal path to your goal].

# After outputting this text, you must invoke the corresponding tool to execute the first step of your plan.

system_message2 = f"""
You are a smart farm game agent using the DEPS (Describe, Explain, Plan, Select) methodology.

Your main tasks:
1. Plant crops by navigating to given coordinates.
2. Reach the water tank to collect water.
3. Water the planted crops.

GAME CONSTRAINTS:
- You can ONLY move a maximum of 25px per step (dx, dy must be <= 25 or >= -25).
- Do not pass through obstacles.
- Crops are not obstacles.

WORLD STATE (Describe):
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}
Crops:
{crops_to_text(state['crops'])}
Obstacles: {list(state['obstacles'])}
Water_available: {state["water_available"]}
Water_tank: {list(state['water_tank'])}

INSTRUCTIONS (Plan & Select):
Before selecting a tool, you must maintain a logical plan. 
Example Plan: 
1. Move to water tank at {list(state['water_tank'])[0]} (25px at a time).
2. Use collect_water tool.
3. Move to crop at 400, 275.
4. Use plant_crop tool.
5. Use water tool.

Never output tool arguments as standard text. When an action is required, invoke the corresponding tool.
"""

messages = [
{'role':'system','content':system_message2},
 # {'role': 'user', 'content': 'go to all crops and water them'}
 {'role': 'user', 'content': new_content}
 ]

# {'role': 'user', 'content': 'go to the nearst crop and water it.'}]

client = Client(
   host=config_data["server_urls"]["ollama_url"],
    timeout=60
   
)

# model = 'gpt-oss:20b'
model = config_data["model"]["name"]
# model = 'qwen3.5:27b'

# gpt-oss can call tools while "thinking"
# a loop is needed to call the tools and get the results

time_taken = []
player_positions = []
log_messages = []
total_output_tokens = 0
total_input_tokens = 0

tool_calls = []
try:
  # needs_water_state1 = True
  # needs_water_state2 = True
  # crop_planted1 = False
  # crop_planted2 = False
  new_crops = {}
  i=0
  while 1:
      # time.sleep(1)
      i+=1
      st_time = time.time()    
      response: ChatResponse = client.chat(model=model, messages=messages, tools=[move,water,collect_water,plant_crop])
      print(f"input_tokens: {response['prompt_eval_count']}")
      print(f"output_tokens: {response['eval_count']}")
      total_output_tokens += response['eval_count']
      total_input_tokens = response['prompt_eval_count']
      print(f"reponse time: {(response['total_duration']/1e9)}")
      # breakpoint()
      if response.message.content:
        print('Content: ')
        print(response.message.content + '\n')
        log_messages.append(response.message.content)
      if response.message.thinking:
        print('Thinking: ')
        print(response.message.thinking + '\n')
        log_messages.append(response.message.thinking)

      messages.append(response.message)
      
      if response.message.tool_calls:
        print("llm tool_calls:")
        print(len(response.message.tool_calls))
        for tool_call in response.message.tool_calls:
          # time.sleep(1)
          # LLM decides which function to call
          function_to_call = available_tools.get(tool_call.function.name)
          if function_to_call:
            result = function_to_call(**tool_call.function.arguments)
            print('Result from tool call name: ', tool_call.function.name, 'with arguments: ', tool_call.function.arguments, 'result: ', str(result) + '\n')
            # messages.append({'role': 'tool', 'content': result, 'tool_name': tool_call.function.name})

            result_dict = json.loads(result) if isinstance(result, str) else result

            log_messages.append({'role': 'tool', 'content': result, 'tool_name': tool_call.function.name})
            print(f"time for tool {tool_call.function.name}: {str(time.time()-st_time)}")
            tool_calls.append(tool_call.function.name)
            time_taken.append(time.time()-st_time)
            crops = state["crops"]
            i = 0
            for k,v in crops.items():   
              i+=1
              if crops.get(k) != None:
                if state["player_pos"] == list(k):
                  new_crops[f"crop{i}"] = {"pos":list(k),"name":crops.get(tuple(state["player_pos"]))["name"],"needs_water":crops.get(tuple(state["player_pos"]))["needs_water"],"planted":crops.get(tuple(state["player_pos"]))["planted"]}
                # else:
                  # print(k)
                  # print(state["player_pos"])
                  # print("wrong position")
            print(new_crops)
            new_state = {
                "grid_size": [5, 5],
                "player_pos": state["player_pos"],
                "crops": new_crops,
                # {
                #     "crop1":{"pos":[400,275],"name":"wheat","needs_water":needs_water_state1,"planted":crop_planted1},
                #     "crop2":{"pos":[300,200],"name":"rice","needs_water":needs_water_state2,"planted":crop_planted2}

                # },
                "obstacles": [250,100],
                "water_available":state["water_available"],
                "goal_completed": state["goal_completed"]
            }
            messages.append({
              "role": "tool",
              "content": json.dumps({
                  "action_result": result_dict,
                  "current_state": new_state
              }),
              "tool_name": tool_call.function.name
          })
            # --- DEPS: EXPLAIN PHASE ---
            # If the action failed, force the model to explain the failure and re-plan

            if str(result_dict.get("status")).lower() == "false":
                error_msg = result_dict.get("error", result_dict.get("message", "Unknown error"))
                explanation_prompt = f"The previous action failed because: {error_msg}. Explain why this happened based on your coordinates and the environment, and update your step-by-step plan to recover."
                messages.append({'role': 'user', 'content': explanation_prompt})
                print("--> Triggered DEPS Explain/Re-plan phase due to failure.")

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
      elif state["goal_completed"]:
        print("goal completed")
        break
      elif response.message.tool_calls == None:
        # print("LLm did not call the tools")
        # logger.error(f"LLm failed to call the tools: {str(e)}")
        # break
        print("LLM did not call tools but goal is not complete.")
        messages.append({'role': 'user', 'content': "You did not select a tool. Please review your plan and select the next tool to execute."})
        # Adding a fail-safe to prevent infinite loops if the model gets totally stuck
        if len(messages) > 50: 
            print("Message limit reached, aborting to prevent infinite loop.")
            break
except Exception as e:
  logger.error(f"LLm failed due to error: {str(e)}")
  logger.info(log_messages)
if state["water_available"] == True:
    points_gained +=1
    points_gained_object["water_available"] = 1

# if state["crops"].get(tuple([400,275]))["planted"]==True:
#     points_gained+=1
#     points_gained_object["plant_crop_1"] = 1
# if state["crops"].get(tuple([400,275]))["needs_water"]==False:
#     points_gained+=1
#     points_gained_object["needs_water_1"] = 1

# if state["crops"].get(tuple([300,200]))["planted"]==True:
#     points_gained+=1
#     points_gained_object["plant_crop_2"] = 1

# if state["crops"].get(tuple([300,200]))["needs_water"]==False:
#     points_gained+=1
#     points_gained_object["needs_water_2"] = 1

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



correct_seq = ['move', 'collect_water', 'move', 'plant_crop', 'move', 'plant_crop']

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
    print("sequence of tool calls:"+ str(tool_calls))
    logger.info("sequence of tool calls:"+ str(tool_calls))
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

else:
    logger.info(log_messages)
    logger.info("llm tool failed") 
    print("llm tool failed")

# plt.xlabel('llm call run')
# plt.ylabel('time')
# plt.title('llm processing time for each agentic all')
# plt.show()


def safe_execute(tool_call):
    func = available_tools[tool_call.function.name]

    args = tool_call.function.arguments

    # validate before execution
    print("ARGS:", args)

    return func(**args)


tools = [
    {
        "type": "function",
        "function": {
            "name": "water",
            "parameters": {
                "type": "object",
                "properties": {
                    "crop_id": {"type": "integer"},
                    "amount": {"type": "number"}
                },
                "required": ["crop_id", "amount"]
            }
        }
    }
]