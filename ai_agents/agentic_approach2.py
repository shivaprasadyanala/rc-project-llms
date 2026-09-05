
import random
import requests
import time
import matplotlib.pyplot as plt
import numpy as np
from a_star_algo import astar
from ollama import Client
from ollama._types import ChatResponse
import json
import logging
import yaml,os,sys
from speech_to_text import audio_text
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

# log_file_name = config_data["log_file"]["name"]
log_file_name = f"{model}"
f_log_file_name = log_file_name.replace(":","_").replace(".","_")
formatted_log_file_name = f"{f_log_file_name}.log"

log_file_folder_path = os.path.join(log_folder, formatted_log_file_name)


log_file_name = config_data["log_file"]["name"]
logging.basicConfig(filename=log_file_folder_path, encoding='utf-8', level=logging.INFO,format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True


url = config_data["server_urls"]["game_state_url"]

url2 = config_data["server_urls"]["whisper_url"]

new_content = "collect water , plant the crops and water them."
# if config_data["speech"]["user_input"]:
#     new_content = audio_text
# else:
#     st_time = time.time()
#     with open("plant_crops_audio.m4a", "rb") as f:
#         response = requests.post(url2, files={"file": f})

#     print(response.json()["text"])

#     print(time.time()-st_time)
#     logger.info(f"time taken for api call + model: {time.time()-st_time}")
#     print("time_take by model")
#     model_time = response.json()["time_taken"]
#     print(response.json()["time_taken"])
#     logger.info(f"time taken for audio by model: {model_time}")

#     new_content = response.json()["text"]

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
    },

    # Obstacles as a set for fast lookup
    "obstacles": [[250, 100]],
    "water_available":False,
    "water_tank":[75,250],

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
      if crops[crop[0],crop[1]]["needs_water"] == False:
        value+=1
    print("value of goal completed:" + str(value))
    if value ==2:
        state["goal_completed"]= True
    return state["goal_completed"]


# set_crop_state()
# breakpoint()
# def crops_parser(crops):
#     i = 0
#     new_crops = {}
#     for k,v in crops.items(): 
#         i+=1
#         if crops.get(k) != None:
#             # if state["player_pos"] == list(k):
#             new_crops[f"crop{i}"] = {"pos":list(k),"name":crops.get(k)["name"],"needs_water":crops.get(k)["needs_water"],"planted":crops.get(k)["planted"]}
#     return new_crops
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
# cro = {(400, 275): {'name': 'wheat', 'planted': False, 'needs_water': True}, (300, 200): {'name': 'rice', 'planted': True, 'needs_water': True}}
# print(crops_parser(cro))

# breakpoint()
player_positions = []

def api_call(current_state,tool="none"):
    # Parse crops and format the state
    
    new_crops = crops_parser(current_state["crops"])
    player_positions.append(current_state["player_pos"])
    # Create a deep copy so future LLM moves don't overwrite this data 
    # before the background thread has a chance to send it
    state_to_send = copy.deepcopy(current_state)
    state_to_send["crops"] = new_crops
    
    # Push to background thread instantly
    if tool=="follow_path":
        print("sleeping....")
        time.sleep(0.25)
    requests.post(url, json=state_to_send, headers=headers)

follow_path_steps = 0

def follow_path(start_px: tuple[int, int], goal_px: tuple[int, int], obstacles_px: list[tuple[int, int]]) -> str:
    global follow_path_steps
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
        "status":"false",
        "action":"follow_path",
        "message": "goal is an obstacle"
        })
    
    
    path = astar(start_px, goal_px, obstacles_px)
    print(f"Path found: {path}")
    for step in path:
        state["player_pos"] = [step[0], step[1]]
        follow_path_steps += 1
        api_call(state,"follow_path")
    return json.dumps({
        "status":"true",
        "action":"follow_path",
        "message": "followed path to the goal"
        })

# print(follow_path((200,100),(400,275),[(250, 100),(75, 250),(200,100),(400,275),(300,200)]))
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
    pos = tuple(state["player_pos"])
    print(pos)
    crop = state["crops"].get(pos)
    print(crop)
    if not crop:
        return "No crop here"

    if not crop["needs_water"]:
        # return "Crop already watered"
        return json.dumps({
        "status":"false",
        "action":"water",
        "message": "crop already watered"
        })

    if not crop["planted"]:
        # invalid_moves+=1
        # invalid_move_object["crop not planted"] = invalid_move_object.get("crop not planted", 0) + 1
        return json.dumps({
        "status":"false",
        "action":"water",
        "message": "crop not planted"
        })

    crop["needs_water"] = False
    state["goal_completed"] = set_crop_state()
    api_call(state,"follow_path")
    # return "Crop watered successfully"
    return json.dumps({
        "status":"true",
        "action":"water",
        "message": "crop watered successfully"
        })


def collect_water()-> str:
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
    api_call(state,"follow_path")
    # print("in collect water tool.............")
    return json.dumps({
        "status":"true",
        "action":"collect water",
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
    new_x = state["player_pos"][0] + int(dx)
    new_y = state["player_pos"][1] + int(dy)

    # Bounds check
    if not (0 <= new_x < state["grid_size"][0] and
            0 <= new_y < state["grid_size"][1]):
        return json.dumps({
        "status":"false",
        "action":"move",
        "player_pos": state["player_pos"],
        "error":"Blocked: out of bounds"
        })

    # Obstacle check
    if (new_x, new_y) in state["obstacles"]:
        return json.dumps({
        "status":"false",
        "action":"move",
        "player_pos": state["player_pos"],
        "error":"Blocked: obstacle"
        })

    state["player_pos"] = [new_x, new_y]
    # return f"game character moved to {(new_x, new_y)}"
    return json.dumps({
        "status":"true",
        "action":"move",
        "player_pos": state["player_pos"]
    })
def check_player_position(crops,x,y,sx,sy):
    is_correct_position = False
    for k,v in crops.items():  
        if (x == k[0] and y == k[1]) and (x == sx and y == sy):
            is_correct_position = True 
    return is_correct_position

def plant_crop(x:int, y:int)-> str:
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

    is_correct_position = check_player_position(state["crops"],new_x,new_y,x,y)

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
    api_call(state,"follow_path")
    return json.dumps({
        "status": True,
        "action": "plant_crop",
        "position": [x, y],
        "planted": True
    })



def api_worker():
    print("API worker started")
    while True:
        try:

            # 1. Try to get a task
            state_snapshot = task_queue.get(timeout=45) 
            # print("state: "+str(state_snapshot) )
        except queue.Empty:
            print("No more tasks. Worker exiting.")
            break # Exit the loop if no tasks arrive for 30 seconds
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



available_tools = {"follow_path":follow_path,"water":water,"collect_water":collect_water,"plant_crop":plant_crop}
# available_tools = {"follow_path":follow_path,"water":water,"astar":astar,"collect_water":collect_water,"plant_crop":plant_crop}


points_gained = 0
points_gained_object = {}

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
# and not allowed to pass through the crops and water tank they are obstacles.
messages = [
{'role':'system','content':system_message2},
 # {'role': 'user', 'content': 'go to all crops and water them'}
 {'role': 'user', 'content': new_content}
 ]

# {'role': 'user', 'content': 'go to the nearst crop and water it.'}]

client = Client(
   host=config_data["server_urls"]["ollama_url"]
   
)
# model = 'gpt-oss:20b'
# model = config_data["model"]["name"]
# model = 'qwen3.5:27b'

# gpt-oss can call tools while "thinking"
# a loop is needed to call the tools and get the results

time_taken = []
agent_messages = []
total_output_tokens = 0
total_input_tokens = 0
tool_calls = []
MAX_ITERATIONS = 80          # hard cap so runaway gpt-oss reasoning loops end cleanly
MAX_TEXT_RETRIES = 3
try:

    new_crops = {}
    for iteration in range(MAX_ITERATIONS):
        # Context trimming: keep system + first user message + recent history
        # so the path/goal is not dropped mid-run.
        if len(messages) > 30:
            messages = messages[:2] + messages[-24:]
        st_time = time.time()    
        response: ChatResponse = client.chat(model=model, messages=messages, tools=[follow_path,water,collect_water,plant_crop])
        print(f"input_tokens: {response['prompt_eval_count']}")

        print("Prompt evaluation time:",response["prompt_eval_duration"] / 1e9, "seconds")
        logger.info(f"Prompt evaluation time:{response['prompt_eval_duration'] / 1e9:.2f}")

        print("Generation time:",response["eval_duration"] / 1e9, "seconds")
        logger.info(f"Generation time: {response['eval_duration'] / 1e9:.2f}")

        print(f"output_tokens: {response['eval_count']}")

        total_output_tokens += response['eval_count']
        total_input_tokens += response['prompt_eval_count']
        print(f"response time: {(response['total_duration']/1e9)}")
        logger.info(f"response time: {response['total_duration'] / 1e9:.2f}")


        if response.message.content:
          print('Content: ')
          print(response.message.content + '\n')
          # agent_messages.append(response.message.content)
          logger.info(f"´content : {response.message.content}")
        if response.message.thinking:
          print('Thinking: ')
          print(response.message.thinking + '\n')
          # agent_messages.append(response.message.thinking)
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
                print("Executing tool instantly in Python:", tool_call.function.name)
                # 1. Execute instantly. (Network calls are sent to the queue inside the tool)
                real_result_json = function_to_call(**tool_call.function.arguments)
              except Exception as e:
                real_result_json = json.dumps({"status":"false", "message": f"{str(e)}"})
              
              print("tool result:")
              print(real_result_json)
              logger.info(f"tool_result: {str(real_result_json)}") 
              if "false" not in real_result_json:
                tool_calls.append(tool_call.function.name)
                time_taken.append(time.time()-st_time)
              # 2. Parse the result back to a dict for the LLM context
              # real_result = json.loads(real_result_json) if isinstance(real_result_json, str) else real_result_json
              real_result = real_result_json
                
              # 3. Get the correct crop state (Make sure crops_parser logic is correct!)
              new_crops = crops_parser(state["crops"])
              new_state = {
                "grid_size": [800, 600],
                "player_pos": state["player_pos"],
                "crops": new_crops,
                "obstacles": state["obstacles"],
                "water_available": state["water_available"],
                "goal_completed": state["goal_completed"]
                }
            
              # 5. Tell the LLM exactly what happened
              messages.append({
                "role": "tool",
                "content": json.dumps({
                    "action_result": real_result,
                    "current_state": new_state
                }),
                "name": tool_call.function.name
              })

              # new_state["task"] = new_content
              # new_task_state = new_state
              # response = requests.post(url, json=new_task_state, headers=headers)
              # print(response)
            else:
              print(f'Tool {tool_call.function.name} not found')
              messages.append({'role': 'tool', 'content': f'Tool {tool_call.function.name} not found', 'tool_name': tool_call.function.name})
        elif state["goal_completed"]:
          print("goal completed")
          break
        elif not response.message.tool_calls:
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
    "grid_size": [800, 600],
            "player_pos": [200,100],
            "crops": reset_crop,
            "obstacles": state["obstacles"][0],
            "water_available":False,
            "goal_completed": state["goal_completed"]
        }
task_queue.put(reset_state)

# response = requests.post(url, json=reset_state, headers=headers)



print(time_taken)
if len(time_taken)>0 and len(tool_calls)>0:
    print("No of llms calls:-")
    print(len(time_taken) + follow_path_steps)
    logger.info(f"No of llms calls: {len(time_taken) + follow_path_steps}")
    result = [tool_calls[0]]
    for action in tool_calls[1:]:
        if action != result[-1]:
            result.append(action)
    tool_calls_final = result
    print("sequence of tool calls:"+ str(tool_calls_final))

    print("player positons:")
    print(player_positions)
    logger.info(f"player_positions: {player_positions}")

    print(f"points gained by agent: {str(points_gained)}")
    logger.info(f"points gained by agent: {str(points_gained)}")
    print(f"points gained object: {str(points_gained_object)}")
    logger.info(f"points gained object: {str(points_gained_object)}")

    logger.info(f"time taken values: {time_taken}")
    print("total input tokens: "+str(total_input_tokens))
    print("total output tokens: "+str(total_output_tokens))
    logger.info("total input tokens: "+str(total_input_tokens))
    logger.info("total output tokens: "+str(total_output_tokens))
else:
    logger.info("llm tool failed") 
    print("llm tool failed")
    print("points gained by agent: 0")
    logger.info("points gained by agent: 0")


