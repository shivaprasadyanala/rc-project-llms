
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
log_folder = "../../experiments/test_logs_few_shot"
os.makedirs(log_folder, exist_ok=True)

# log_file_name = config_data["log_file"]["name"]
log_file_name = f"{model}"
f_log_file_name = log_file_name.replace(":","_").replace(".","_")
formatted_log_file_name = f"{f_log_file_name}.log"

log_file_folder_path = os.path.join(log_folder, formatted_log_file_name)

logging.basicConfig(filename=log_file_folder_path, encoding='utf-8', level=logging.INFO,format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True

logger.info("model_used_for_few_shots: "+ model)

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
      if  crops[crop[0],crop[1]]["planted"] == True and crops[crop[0],crop[1]]["needs_water"] == False:
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
        invalid_move_object["no crop"] = invalid_move_object.get("no crop", 0) + 1
        return {
        "status":"false",
        "action":"water",
        "message": "no crop here"
        }
    if not crop["planted"]:
        invalid_moves+=1
        invalid_move_object["crop not planted"] = invalid_move_object.get("crop not planted", 0) + 1
        return {
        "status":"false",
        "action":"water",
        "message": "crop not planted"
        }

    if not crop["needs_water"]:
        invalid_moves+=1
        # return "Crop already watered"
        invalid_move_object["crop already watered"] = invalid_move_object.get("crop already watered", 0) + 1
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

    water_tank = (state["water_tank"])
    print(water_tank)
    if new_x != water_tank[0] or new_y != water_tank[1]:
        invalid_moves +=1
        invalid_move_object["no water tank here"] = invalid_move_object.get("no water tank here", 0) + 1
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
        invalid_move_object["out of bounds"] = invalid_move_object.get("out of bounds", 0) + 1

        return json.dumps({
        "status":"false",
        "action":"move",
        "player_pos": state["player_pos"],
        "error":"Blocked: out of bounds"
        })

    # Obstacle check
    if (new_x, new_y) in state["obstacles"]:
        invalid_moves+=1
        invalid_move_object["blocked obstacle"] = invalid_move_object.get("blocked obstacle", 0) + 1
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
        invalid_move_object["No crop here"] = invalid_move_object.get("No crop here", 0) + 1
        return json.dumps({
            "status": False,
            "error": "No crop here",
            "position": [x, y]
        })

    if crop["planted"]:
        invalid_move_object["Already planted"] = invalid_move_object.get("Already planted", 0) + 1
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



system_message2 = f"""

You are a Smart Farm game agent.

## Objective

Your goals are:

1. Plant every crop that is not yet planted.
2. If you do not have water, reach the water tank to collect water.
3. After collecting water, plant crops.
4. Always verify whether a crop is already planted before attempting to plant it.

## Rules

- The WORLD STATE is the single source of truth.
- Never assume previous actions succeeded.
- Always inspect the latest WORLD STATE.
- Move exactly 25 pixels per action.
- Only move in one cardinal direction (up, down, left, right).
- Never move diagonally.
- Never move through:
  - crops
  - water tanks
  - obstacles
- Plan a valid path around obstacles.
- If water_available is False, prioritize reaching the water tank.
- If standing on an unplanted crop and water is available, plant it.
- Never plant an already planted crop.
- After planting, verify in the next WORLD STATE that the crop is marked planted=True.
- Call exactly one tool in every response.
- Never output tool arguments as text.
- Never explain your reasoning.

## Decision Priority

Follow this order every turn:

1. Check whether all crops are already planted.
2. If yes, stop.
3. Otherwise check water_available.
4. If False, move toward the water tank.
5. If True, move toward the nearest unplanted crop.
6. If already on the crop, plant it.
7. Wait for the updated WORLD STATE before deciding again.

---
{available_tools}

## Example 1

WORLD STATE

Player position:
(25,25)

Water_available:
False

Water tank:
[(75,25)]

Crop:
(125,25)
planted=False

Assistant:
→ Call the move tool once toward the water tank.

---

## Example 2

WORLD STATE

Player position:
(75,25)

Water_available:
True

Crop:
(125,25)
planted=False

Assistant:
→ Call the move tool once toward the crop.

---

## Example 3

WORLD STATE

Player position:
(125,25)

Water_available:
True

Crop:
(125,25)
planted=False

Assistant:
→ Call the plant tool.

---

## Example 4

WORLD STATE

Player position:
(125,25)

Crop:
(125,25)
planted=True

Assistant:
→ Do not plant again. Move toward the next unplanted crop.

---
WORLD STATE

Player position:
(125,25)

Water_available:
True

Crop:
(125,25)
planted=True

Assistant:
→ Call the water tool.
---

## Example 5

WORLD STATE

Player:
(25,25)

Crop:
(75,25)

Obstacle:
[(50,25)]

Assistant:
→ Call one move tool that begins navigating around the obstacle.

---
## CURRENT WORLD STATE

CURRENT STATE (authoritative):

Grid size:
{state['grid_size']}

Player position:
{tuple(state['player_pos'])}

Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}

Water_available:
{state["water_available"]}

Water_tank:
{list(state['water_tank'])}

## Available Tools

{available_tools}

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
# model = config_data["model"]["name"]
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
  while i< 50:
      print("i value:")
      print(i)
      if len(messages) > 10:
          messages = messages[:2] + messages[-6:]
      # time.sleep(1)
      i+=1
      st_time = time.time()    
      # response: ChatResponse = client.chat(model=model, messages=messages, tools=[move,water,collect_water,plant_crop],think=True,options={"temperature": 0.0})
      response: ChatResponse = client.chat(model=model, messages=messages, tools=[move,water,collect_water,plant_crop])

      print(f"input_tokens: {response['prompt_eval_count']}")
      print(f"output_tokens: {response['eval_count']}")
      total_output_tokens += response['eval_count']
      total_input_tokens = response['prompt_eval_count']
      print(f"reponse time: {(response['total_duration']/1e9)}")
      print("reponse::")
      print(response.message)
      # breakpoint()
      if response.message.content:
        print('Content: ')
        print(response.message.content + '\n')
        # log_messages.append(response.message.content)
        logger.info(f"content : {response.message.content}")
      if response.message.thinking:
        print('Thinking: ')
        print(response.message.thinking + '\n')
        # log_messages.append(response.message.thinking)
        logger.info(f"thinking : {response.message.thinking}")

      messages.append(response.message)
      
      if response.message.tool_calls:
        print("llm tool_calls:")
        print(len(response.message.tool_calls))
        for tool_call in response.message.tool_calls:
          # time.sleep(1)
          # LLM decides which function to call
          function_to_call = available_tools.get(tool_call.function.name)
          result_dict = ""
          if function_to_call:
            try:
                result = function_to_call(**tool_call.function.arguments)
                result_dict = result
            except Exception as e:
                result_dict = json.dumps({"status":"false", "message": f"{str(e)}"})
            print('Result from tool call name: ', tool_call.function.name, 'with arguments: ', tool_call.function.arguments, 'result: ', result_dict + '\n')
            # messages.append({'role': 'tool', 'content': result, 'tool_name': tool_call.function.name})
            # log_messages.append({'role': 'tool', 'content': result, 'tool_name': tool_call.function.name})
            logger.info(f"tool_res : {json.dumps(result_dict)}")
            print(f"time for tool {tool_call.function.name}: {str(time.time()-st_time)}")
            tool_calls.append(tool_call.function.name)
            time_taken.append(time.time()-st_time)
            crops = state["crops"]
            
            j = 0
            for k,v in crops.items():   
              j+=1
              if crops.get(k) != None:
                if state["player_pos"] == list(k):
                  new_crops[f"crop{j}"] = {"pos":list(k),"name":crops.get(tuple(state["player_pos"]))["name"],"needs_water":crops.get(tuple(state["player_pos"]))["needs_water"],"planted":crops.get(tuple(state["player_pos"]))["planted"]}
                # else:
                  # print(k)
                  # print(state["player_pos"])
                  # print("wrong position")
            print(new_crops)
            new_state = {
                "grid_size": [5, 5],
                "player_pos": state["player_pos"],
                "crops": new_crops,
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
        break
      # elif response.message.tool_calls == None:
      #   print("LLm did not call the tools")
      #   logger.error(f"LLm failed to call the tools: {str(e)}")
      #   break
      elif response.message.tool_calls == None:
        print("LLM did not call tools but goal is not complete.")
        logger.info(f"LLM did not call tools but goal is not complete.")
        # messages.append({'role': 'user', 'content': "You did not select a tool. Please review your plan and select the next tool to execute."})
        # # Adding a fail-safe to prevent infinite loops if the model gets totally stuck
        # if len(messages) > 50: 
        #     print("Message limit reached, aborting to prevent infinite loop.")
        #     logger.error(f"Message limit reached, aborting to prevent infinite loop.")
        break

except Exception as e:
  logger.error(f"LLm failed due to error: {str(e)}")
  print(f"LLm failed due to error: {str(e)}")
  # logger.info(log_messages)
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

else:
    # logger.info(log_messages)
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