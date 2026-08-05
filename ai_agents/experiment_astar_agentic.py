
from collections import defaultdict
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
import yaml
import os
import sys
import argparse
from speech_to_text import audio_text
from game_states_gemini import states

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
log_folder = "../../experiments/test_logs_astar"
os.makedirs(log_folder, exist_ok=True)

log_file_name = f"{model}"
f_log_file_name = log_file_name.replace(":", "_").replace(".", "_")
formatted_log_file_name = f"{f_log_file_name}.log"

log_file_folder_path = os.path.join(log_folder, formatted_log_file_name)

logging.basicConfig(filename=log_file_folder_path, encoding='utf-8',
                    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True

logger.info("model_used_for_astar: " + model)

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

game_states = []
for state_key, state in states.items():
    state_result = defaultdict(dict)


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
            invalid_move_object["no crop"] = invalid_move_object.get(
                "no crop", 0) + 1
            return json.dumps({
                "status": "false",
                "action": "water",
                "message": "no crop here"
            })
        if not crop["planted"]:
            invalid_moves += 1
            invalid_move_object["crop not planted"] = invalid_move_object.get(
                "crop not planted", 0) + 1
            return json.dumps({
                "status": "false",
                "action": "water",
                "message": "crop not planted"
            })

        if not crop["needs_water"]:
            invalid_moves += 1
            # return "Crop already watered"
            invalid_move_object["crop already watered"] = invalid_move_object.get(
                "crop already watered", 0) + 1
            return json.dumps({
                "status": "false",
                "action": "water",
                "message": "crop already watered"
            })

        crop["needs_water"] = False

        state["goal_completed"] = set_crop_state()
        # return "Crop watered successfully"
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
            invalid_move_object["no water tank here"] = invalid_move_object.get(
                "no water tank here", 0) + 1
            return json.dumps({
                "status": "false",
                "action": "collect water",
                "message": "no water tank here",
                "water_available": state["water_available"]
            })

        # water_tank_y = state["water_tank"][1]
        state["water_available"] = True
        # print("in collect water tool.............")
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

        # Bounds check
        if int(dx) > 0 and int(dy) > 0:
            invalid_moves += 1
            invalid_move_object["diagonal_move"] = invalid_move_object.get(
                "diagonal_move", 0) + 1
            return json.dumps({
                "status": "false",
                "action": "move",
                "player_pos": state["player_pos"],
                "error": "diagonal move not allowed"
            })
        VALID_PAIRS = {(0, -25), (0, 25), (-25, 0), (25, 0)}
        if (dx, dy) not in VALID_PAIRS:
            invalid_moves += 1
            invalid_move_object["move tool argument values are not 25px"] = invalid_move_object.get(
                "move tool argument values are not 25px", 0) + 1
            return json.dumps({
                "status": "false",
                "action": "move",
                "player_pos": state["player_pos"],
                "error": "invalid tool argument values check the rules again."
            })
        if not (0 <= new_x < state["grid_size"][0] and
                0 <= new_y < state["grid_size"][1]):
            invalid_moves += 1
            invalid_move_object["out of bounds"] = invalid_move_object.get(
                "out of bounds", 0) + 1

            return json.dumps({
                "status": "false",
                "action": "move",
                "player_pos": state["player_pos"],
                "error": "Blocked: out of bounds"
            })

        # Obstacle check
        if (new_x, new_y) in state["obstacles"]:
            invalid_moves += 1
            invalid_move_object["blocked obstacle"] = invalid_move_object.get(
                "blocked obstacle", 0) + 1
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
            # return f"game character moved to {(new_x, new_y)}"
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

        is_correct_position = check_player_postion(
            state["crops"], new_x, new_y, x, y)

        if not is_correct_position:
            return json.dumps({
                "status": False,
                "error": "the player is not at the crop.",
                "position": [x, y]
            })

        if not crop:
            invalid_moves += 1
            invalid_move_object["No crop here"] = invalid_move_object.get(
                "No crop here", 0) + 1
            return json.dumps({
                "status": False,
                "error": "No crop here",
                "position": [x, y]
            })

        if crop["planted"]:
            invalid_move_object["Already planted"] = invalid_move_object.get(
                "Already planted", 0) + 1
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


    available_tools = {"move": move, "water": water, "astar": astar,
                       "collect_water": collect_water, "plant_crop": plant_crop}

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
    and not allowed to pass through the crop, water tank, they are obstacles.

    Never output tool arguments as text, JSON, markdown, or code blocks.
    When an action is required, invoke the corresponding tool. 
    If a tool is available, emitting its arguments in text form is always incorrect.

    Tools available:
    {available_tools}

    """

    messages = [
        {'role': 'system', 'content': system_message2},
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
    tool_calls_array = []
    player_positions = []
    # agent_messages = []
    total_output_tokens = 0
    total_input_tokens = 0
    try:
        new_crops = {}
        while True:
            if len(messages) > 10:
                messages = messages[:2] + messages[-8:]
            st_time = time.time()
            response: ChatResponse = client.chat(model=model, messages=messages, tools=[
                                                 move, water, astar, collect_water, plant_crop])
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
              for tool_call in response.message.tool_calls:
                # LLM decides which function to call
                function_to_call = available_tools.get(tool_call.function.name)
                real_result_json = ""
                if function_to_call:
                  try:
                    result = function_to_call(**tool_call.function.arguments)
                    print('Result from tool call name: ', tool_call.function.name, 'with arguments: ',
                          tool_call.function.arguments, 'result: ', str(result) + '\n')
                    real_result_json = result
                  except Exception as e:
                    real_result_json = json.dumps(
                        {"status": "false", "message": f"Error in tool call: {str(e)}"})
                  logger.info(
                      f"tool: {str(tool_call.function.name)}  result: {str(real_result_json)}")
                  print(
                      f"tool: {str(tool_call.function.name)}  result: {str(real_result_json)}")
                  print(
                      f"time for tool {tool_call.function.name}: {str(time.time()-st_time)}")
                  if "false" not in real_result_json:
                    tool_calls_array.append(tool_call.function.name)
                    time_taken.append(time.time()-st_time)
                  crops = state["crops"]

                  j = 0
                  for k, v in crops.items():
                    j += 1
                    if crops.get(k) != None:
                      if state["player_pos"] == list(k):
                        new_crops[f"crop{j}"] = {"pos": list(k), "name": crops.get(tuple(state["player_pos"]))["name"], "needs_water": crops.get(
                            tuple(state["player_pos"]))["needs_water"], "planted": crops.get(tuple(state["player_pos"]))["planted"]}
                  print(new_crops)
                  new_state = {
                      "grid_size": [5, 5],
                      "player_pos": state["player_pos"],
                      "crops": new_crops,
                      "obstacles": [250, 100],
                      "water_available": state["water_available"],
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
                  new_state["task"] = new_content
                  new_task_state = new_state
                  response = requests.post(
                      url, json=new_task_state, headers=headers)
                  print(response)
                else:
                  print(f'Tool {tool_call.function.name} not found')
                  messages.append(
                      {'role': 'tool', 'content': f'Tool {tool_call.function.name} not found', 'tool_name': tool_call.function.name})
            elif state["goal_completed"]:
              break
            elif response.message.tool_calls == None:
              print("LLM did not call tools but goal is not complete.")
              logger.info(f"LLM did not call tools but goal is not complete.")
              break
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
        print("total input tokens: "+str(total_input_tokens))
        print("total output tokens: "+str(total_output_tokens))
        logger.info("total input tokens: "+str(total_input_tokens))
        logger.info("total output tokens: "+str(total_output_tokens))
    else:
        print(f"points gained by agent: {str(points_gained)}")
        logger.info(f"points gained by agent: {str(points_gained)}")
        logger.info("llm tool failed")
        print("llm tool failed")
    game_states.append(state_result)

logger.info(f"game_states: {game_states}")
