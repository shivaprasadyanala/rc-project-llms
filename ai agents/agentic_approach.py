# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "gpt-oss",
#     "ollama",
#     "rich",
# ]
# ///
import random
import requests
import time
import matplotlib.pyplot as plt
import numpy as np
from a_star_algo import astar
from ollama import Client
from ollama._types import ChatResponse

# start = (50, 75)
# goal = (150, 125)

# obstacles = [
#     (75, 75),
#     (100, 75),
#     (125, 75)
# ]

# path = astar(start, goal, obstacles, grid_width=20, grid_height=20)

# print(path)
url = "http://localhost:3000/post_game_state/"

url2 = "http://hal9000.skim.th-owl.de:8003/transcribe"

st_time = time.time()
with open("record_game.m4a", "rb") as f:
    response = requests.post(url2, files={"file": f})

print(response.json()["text"])

print(time.time()-st_time)
print("time_take by model")
print(response.json()["time_taken"])

new_content = response.json()["text"]

headers = {
"Content-Type": "application/json"
}


# from rich import print






def move_left()-> str:
  """
    move the game character to right and get the number of moved units
    Args:
        None
    Returns:
      str: The number of units moved by the game character
  """
  units = list(range(-10, 35))

  moved_units = random.choice(units)
  return f"The character moved to the right by:{moved_units}"


def move_right()-> str:
  """
    move the game character to right and get the number of moved units
    Args:
        None
    Returns:
      str: The number of units moved by the game character
  """
  units = list(range(-10, 35))

  moved_units = random.choice(units)
  return f"The character moved to the right by:{moved_units}"

def move_up()-> str:
  """
    move the game character up and get the number of moved units
    Args:
        None
    Returns:
      str: The number of units moved by the game character
  """
  units = list(range(-10, 35))

  moved_units = random.choice(units)
  return f"The character moved up by:{moved_units}"

def move_down()-> str:
  """
    move the game character right and get the number of moved units
    Args:
        None
    Returns:
      str: The number of units moved by the game character
  """
  units = list(range(-10, 35))

  moved_units = random.choice(units)
  return f"The character moved down by:{moved_units}"

state = {
    "grid_size": (800, 600),

    # Player
    "player_pos": [200, 100],  # use list for mutability

    # Crops indexed by position
    "crops": {
        (400, 275): {"needs_water": True},
        (300, 200): {"needs_water": True},
    },

    # Obstacles as a set for fast lookup
    "obstacles": {(250, 100)},

    # Goal tracking
    "goal_completed": False
}

def set_crop_state():
    """
    sets the water state of the crop
    """
    crops = state["crops"]
    is_goal_completed = False
    for crop in crops:
      # print("crop:")
      # print(crop)
      is_goal_completed = is_goal_completed and crop["needs_water"]
    state["goal_completed"]= is_goal_completed
    return is_goal_completed
    
def water():
    """
      water the crop and changes the state of water accordinglys
      Args:
          Nones
      Returns:
        str: response of the result
    """
    pos = tuple(state["player_pos"])
    print(pos)
    crop = state["crops"].get(pos)
    print(crop)
    if not crop:
        return "No crop here"

    if not crop["needs_water"]:
        return "Crop already watered"

    crop["needs_water"] = False

    state["goal_completed"] = set_crop_state()
    return "Crop watered successfully"


# water()

# breakpoint()

def crops_to_text(crops):
    lines = []
    for pos, info in crops.items():
      lines.append(f"- {pos}: needs_water = {info['needs_water']}")
    return "\n".join(lines)

def move(dx, dy):
    """
      move the game character based on dx and dy values and updates the state variable
      Args:
          dx (int): x value of the coordinate
          dy (int): y value of the coordinate
      Returns:
        str: The number of units moved by the game character
    """
    new_x = state["player_pos"][0] + int(dx)
    new_y = state["player_pos"][1] + int(dy)

    # Bounds check
    if not (0 <= new_x < state["grid_size"][0] and
            0 <= new_y < state["grid_size"][1]):
        return "Blocked: out of bounds"

    # Obstacle check
    if (new_x, new_y) in state["obstacles"]:
        return "Blocked: obstacle"

    state["player_pos"] = [new_x, new_y]
    return f"Moved to {(new_x, new_y)}"



# available_tools = {'move_left':move_left,'move_right':move_right,'move_up':move_up,'move_down':move_down,"move":move,"water":water}
available_tools = {'move_left':move_left,'move_right':move_right,'move_up':move_up,'move_down':move_down,"move":move,"water":water,"astar":astar}



# Think step by step, but only keep minimum draft for each thinking step, with 5 words at most.
#    Return the "Yes" or "No" at the end of the response after a separator ####.


system_message1 = f"""

 
CURRENT STATE (authoritative):
  
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}
  
Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}

  
  move 25pxs and one side at a time
  and not allowed to pass through the crop and crops are not obstacles.
"""

system_message2 = f"""

 
CURRENT STATE (authoritative):
  
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}
  
Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}


  To calculate the distance should use the astar algorithm tool
  move 25pxs and one side at a time
  and not allowed to pass through the crop and crops are not obstacles.

"""

system_message2_ = f"""

 
CURRENT STATE (authoritative):
  
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}
  
Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}

You are a farming strategy agent.
Responsibilities:
- choose goals
- decide priorities
- choose interaction targets

  Your job:
- NEVER compute movement
- NEVER calculate paths
- NEVER to pass through the crop and crops are not obstacles.

Movement is handled by tools.

"""

system_message3 = f"""
You are a deterministic grid-navigation agent.

Your task:
Given the current world state, compute the optimal next movement step toward the target using A* pathfinding.

WORLD STATE:

Grid Size:
{state['grid_size']}

Player Position:
{tuple(state['player_pos'])}

Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}

STRICT RULES:

1. MOVEMENT
- Move exactly 25 pixels per action.
- Only 4-directional movement is allowed:
  UP, DOWN, LEFT, RIGHT
- No diagonal movement.

2. BLOCKED TILES
- Obstacles are blocked.
- Crops are also blocked EXCEPT when the crop is the target destination tile.
- Never move through blocked tiles.
- Never move outside the map.

3. PATHFINDING
- Use A* search for all navigation decisions.
- Minimize total travel distance.
- If multiple paths are equal:
  Prefer:
  UP > LEFT > RIGHT > DOWN

4. RESPONSE RULES
- Return ONLY the next move.
- Do not explain reasoning.
- Do not return coordinates.
- Do not return the full path.

VALID RESPONSES:
UP
DOWN
LEFT
RIGHT
STUCK
"""


messages = [
{'role':'system','content':system_message1},
 # {'role': 'user', 'content': 'go to all crops and water them'}
 {'role': 'user', 'content': new_content}
 ]

# {'role': 'user', 'content': 'go to the nearst crop and water it.'}]

client = Client(
   host="http://hal9000.skim.th-owl.de:11437"
)
# model = 'gpt-oss:120b'
model = "gpt-oss:20b"
# gpt-oss can call tools while "thinking"
# a loop is needed to call the tools and get the results

time_taken = []
while True:
  st_time = time.time()
  print("Hiiii")
  # response: ChatResponse = client.chat(model=model, messages=messages, tools=[ move_left,move_up,move_right,move_down,move,water])
  response: ChatResponse = client.chat(model=model, messages=messages, tools=[move,water,astar])

  if response.message.content:
    print('Content: ')
    print(response.message.content + '\n')
  if response.message.thinking:
    print('Thinking: ')
    print(response.message.thinking + '\n')

  messages.append(response.message)

  if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
      function_to_call = available_tools.get(tool_call.function.name)
      if function_to_call:
        result = function_to_call(**tool_call.function.arguments)
        print('Result from tool call name: ', tool_call.function.name, 'with arguments: ', tool_call.function.arguments, 'result: ', result + '\n')
        messages.append({'role': 'tool', 'content': result, 'tool_name': tool_call.function.name})
        print("state:")
        print(state)
        print("time:"+str(time.time()-st_time))
        time_taken.append(time.time()-st_time)

        print("crops:")
        needs_water_state = True
        crops = state["crops"]
        if crops.get(tuple(state["player_pos"])) != None:
            print("test water state")
            needs_water_state = crops.get(tuple(state["player_pos"]))["needs_water"]
        new_state = {
            "grid_size": [5, 5],
            "player_pos": state["player_pos"],
            "crops": {
                "crop1":{"pos":[400,275],"needs_water":needs_water_state},
                "crop2":{"pos":[300,200],"needs_water":needs_water_state}
            },
            "obstacles": [250,100],
            "goal_completed": state["goal_completed"]
        }
        print("new_state")
        print(new_state)
        response = requests.post(url, json=new_state, headers=headers)
        print(response)
      else:
        print(f'Tool {tool_call.function.name} not found')
        messages.append({'role': 'tool', 'content': f'Tool {tool_call.function.name} not found', 'tool_name': tool_call.function.name})
  elif state["goal_completed"]:
    break
  else:
    # no more tool calls, we can stop the loop
    break

reset_state = {
            "grid_size": [5, 5],
            "player_pos": [200,100],

            "crops": {
                "crop1":{"pos":[400,275],"needs_water":True},
                "crop2":{"pos":[300,200],"needs_water":True}
            },
            "obstacles": [250,100],
            "goal_completed": False
        }
        
response = requests.post(url, json=reset_state, headers=headers)

print(time_taken)

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



plt.plot(time_taken)
plt.xlabel('llm call run')
plt.ylabel('time')
plt.title('llm processing time for each agentic all')
plt.show()

# state = get_game_state()

# while True:
#     prompt = build_prompt(state)
#     action = llm(prompt)          # exactly one tool call
#     state = apply_action(action)  # engine updates position / crops

# while not goal_done:
#     prompt = build_prompt(current_state)
#     tool_call = llm(prompt)        # ONE tool
#     current_state = apply(tool_call)


# You are an autonomous game agent controlling a character on a 2D grid.

# You may call ONLY ONE tool per turn.
# You MUST respond with a tool call and NOTHING ELSE.

# TOOLS:
# - move_up
# - move_down
# - move_left
# - move_right
# - water

# CURRENT STATE (authoritative, complete, and final):

# Grid size: {width}x{height}
# Player position: ({px}, {py})

# Crops:
# {list of crops with coordinates and needs_water}

# Obstacles:
# {list or empty}

# Rules:
# - You must never assume any state not listed above.
# - You must never invent crops or positions.
# - Do NOT call water unless standing on a crop tile that needs water.
# - If no crop needs water, call move_right.

# Decide the next action.