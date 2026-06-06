
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
logger = logging.getLogger(__name__)
logging.basicConfig(filename='example3.log', encoding='utf-8', level=logging.INFO,format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True

url = "http://localhost:3000/post_game_state/"

url2 = "http://hal9000.skim.th-owl.de:8003/transcribe"

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
        (400, 275): {"planted":False,"needs_water": True},
        (300, 200): {"planted":False,"needs_water": True},
        # (200,475): {"planted":False,"needs_water": True},
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
    print(value)
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
    pos = tuple(state["player_pos"])
    print(pos)
    crop = state["crops"].get(pos)
    print(crop)
    if not crop:
        return "No crop here"

    if not crop["needs_water"]:
        # return "Crop already watered"
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
        "water_available": state["water_available"]
       }
    """

    state["water_available"] = True
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

    crop = state["crops"].get((x, y))

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

available_tools = {"move":move,"water":water,"astar":astar,"collect_water":collect_water,"plant_crop":plant_crop}

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
and not allowed to pass through the crop and crops are not obstacles.

Never output tool arguments as text, JSON, markdown, or code blocks.
When an action is required, invoke the corresponding tool. 
If a tool is available, emitting its arguments in text form is always incorrect.

Tools available:
{available_tools}



"""

messages = [
{'role':'system','content':system_message2},
 # {'role': 'user', 'content': 'go to all crops and water them'}
 {'role': 'user', 'content': new_content}
 ]

# {'role': 'user', 'content': 'go to the nearst crop and water it.'}]

client = Client(
   host="http://hal9000.skim.th-owl.de:11437"
   
)
# model = 'gpt-oss:20b'
model = 'gemma4:26b'
# model = 'qwen3.5:27b'

# gpt-oss can call tools while "thinking"
# a loop is needed to call the tools and get the results

time_taken = []
player_positions = []
agent_messages = []
total_output_tokens = 0
total_input_tokens = 0
# try:
while True:
    st_time = time.time()    
    response: ChatResponse = client.chat(model=model, messages=messages, tools=[move,water,astar,collect_water,plant_crop])
    print(f"input_tokens: {response['prompt_eval_count']}")
    print(f"output_tokens: {response['eval_count']}")
    total_output_tokens += response['eval_count']
    total_input_tokens = response['prompt_eval_count']
    print(f"reponse time: {(response['total_duration']/1e9)}")

    if response.message.content:
      print('Content: ')
      print(response.message.content + '\n')
      agent_messages.append(response.message.content)
    if response.message.thinking:
      print('Thinking: ')
      print(response.message.thinking + '\n')
      agent_messages.append(response.message.thinking)

    messages.append(response.message)

    if response.message.tool_calls:
      for tool_call in response.message.tool_calls:
        function_to_call = available_tools.get(tool_call.function.name)
        if function_to_call:
          
          result = function_to_call(**tool_call.function.arguments)
          print('Result from tool call name: ', tool_call.function.name, 'with arguments: ', tool_call.function.arguments, 'result: ', str(result) + '\n')
          # messages.append({'role': 'tool', 'content': result, 'tool_name': tool_call.function.name})
          agent_messages.append({'role': 'tool', 'content': result, 'tool_name': tool_call.function.name})
          print(f"time for tool {tool_call.function.name}: {str(time.time()-st_time)}")
          time_taken.append(time.time()-st_time)

          needs_water_state1 = True

          needs_water_state2 = True
          crop_planted1 = False
          crop_planted2 = False
          crops = state["crops"]
          if crops.get(tuple(state["player_pos"])) != None:
              if state["player_pos"] == [400,275]:
                  needs_water_state1 = crops.get(tuple(state["player_pos"]))["needs_water"]
                  crop_planted1 = crops.get(tuple(state["player_pos"]))["planted"]
                  

              if state["player_pos"] == [300,200]:
                  needs_water_state2 = crops.get(tuple(state["player_pos"]))["needs_water"]
                  crop_planted2 = crops.get(tuple(state["player_pos"]))["planted"]
                  # if crops.get(tuple(state["player_pos"]))["planted"]==True:
                  #     points_gained+=1
                  # if crops.get(tuple(state["player_pos"]))["needs_water"]==False:
                  #     points_gained+=1
              print(needs_water_state1,needs_water_state2)
              print(crop_planted1,crop_planted2)
          

          new_state = {
              "grid_size": [5, 5],
              "player_pos": state["player_pos"],
              "crops": {
                  "crop1":{"pos":[400,275],"needs_water":needs_water_state1,"planted":crop_planted1},
                  "crop2":{"pos":[300,200],"needs_water":needs_water_state2,"planted":crop_planted2}

              },
              "obstacles": [250,100],
              "water_available":state["water_available"],
              "goal_completed": state["goal_completed"]
          }
          messages.append({
            "role": "tool",
            "content": json.dumps({
                "action_result": result,
                "current_state": new_state
            }),
            "tool_name": tool_call.function.name
        })

          print("new_state")
          print(new_state)
          player_positions.append(state["player_pos"])
          response = requests.post(url, json=new_state, headers=headers)
          print(response)
        else:
          print(f'Tool {tool_call.function.name} not found')
          messages.append({'role': 'tool', 'content': f'Tool {tool_call.function.name} not found', 'tool_name': tool_call.function.name})
    elif state["goal_completed"]:
      break
    else:
      break
# except Exception as e:
#   logger.error(f"LLm failed due to error: {str(e)}")
#   logger.info(agent_messages)
if state["water_available"] == True:
    points_gained +=1
    points_gained_object["water_available"] = 1

if state["crops"].get(tuple([400,275]))["planted"]==True:
    points_gained+=1
    points_gained_object["plant_crop_1"] = 1
if state["crops"].get(tuple([400,275]))["needs_water"]==False:
    points_gained+=1
    points_gained_object["needs_water_1"] = 1

if state["crops"].get(tuple([300,200]))["planted"]==True:
    points_gained+=1
    points_gained_object["plant_crop_2"] = 1

if state["crops"].get(tuple([300,200]))["needs_water"]==False:
    points_gained+=1
    points_gained_object["needs_water_2"] = 1


reset_state = {
            "grid_size": [5, 5],
            "player_pos": [200,100],

            "crops": {
                "crop1":{"pos":[400,275],"needs_water":True,"planted":False},
                "crop2":{"pos":[300,200],"needs_water":True,"planted":False},
                # "crop3":{"pos":[200,475],"needs_water":True,"planted":False},
                # "crop4":{"pos":[150,300],"needs_water":True,"planted":False},
                # "crop5":{"pos":[275,325],"needs_water":True,"planted":False}
            },
            "obstacles": [250,100],
            "water_available":False,
            "goal_completed": False
        }


response = requests.post(url, json=reset_state, headers=headers)



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
else:
    logger.info(agent_messages)
    logger.info("llm tool failed") 
    print("llm tool failed")

# plt.xlabel('llm call run')
# plt.ylabel('time')
# plt.title('llm processing time for each agentic all')
# plt.show()

