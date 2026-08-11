
import random
import requests
import time
import matplotlib.pyplot as plt
import numpy as np
from ollama import Client
from ollama._types import ChatResponse
import json
import yaml,os,sys
from speech_to_text import audio_text
from non_trivial_tasks import tasks
from utils import find_final_score
from my_logger import logger,config_data,model
from collections import defaultdict


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
final_result = []
for task in tasks:
    results = defaultdict(lambda: defaultdict(dict))
    for task_name, difficulties in task.items():
        # results[task_name] = {}
        print(f"Task: {task_name}")
        for difficulty, prompts in difficulties.items():
            print(f"  Difficulty: {difficulty}")
            final_score_array = []
            tool_calls_array = []
            tool_call_names = []
            for prompt in prompts:
                task_type =  task_name.replace("_task", "")
                new_content = prompt
                print("Task:")
                print(new_content)
                state = {
                    "grid_size": (800, 600),

                    # Player
                        "player_pos": [200, 100],  # use list for mutability

                    # Crops indexed by position
                    

                    # Obstacles as a set for fast lookup
                    "obstacles": [[250, 100]],
                    "water_available":False,
                    "water_tank":[75,250],

                    # Goal tracking
                    "goal_completed": False
                }

                crops_object = {
                "crops": {
                        (400, 275): {"name":"wheat","is_planted":False,"needs_water": True},
                        (300, 200): {"name":"rice","is_planted":False,"needs_water": True},
                        # (200,475): {"name":"sugarcane","is_planted":False,"needs_water": True},
                    }
                    }

                invalid_moves = 0
                revisits = 0
                visited = set()
                invalid_move_object = {}

                def set_crop_state():
                    """
                    sets the water state of the crop
                    """
                    crops = crops_object["crops"]
                    is_goal_completed = False
                    value = 0
                    for crop in crops:
                      if  crops[crop[0],crop[1]]["is_planted"] == True and crops[crop[0],crop[1]]["needs_water"] == False:
                        value+=1
                    print("value of goal completed:" + str(value))
                    if value ==2:
                        state["goal_completed"] = True
                    return state["goal_completed"]

                def goal_completed(state):
                    """
                    sets the water state of the crop
                    """
                    global task_type
                    crops = crops_object["crops"]

                    is_goal_completed = False
                    if task_type == "plant_crop_water":
                        value = 0
                        for crop in crops:
                          if  crops[crop[0],crop[1]]["is_planted"] == True and crops[crop[0],crop[1]]["needs_water"] == False:
                            value+=1
                        print("value of goal completed:" + str(value))
                        if value ==2:
                            state["goal_completed"] = True
                        return state["goal_completed"]
                    elif task_type == "plant_crop":
                        value = 0
                        for crop in crops:
                          if  crops[crop[0],crop[1]]["is_planted"] == True:
                            value+=1
                        print("value of goal completed:" + str(value))
                        if value ==2:
                            state["goal_completed"] = True
                        return state["goal_completed"]
                    elif task_type == "collect_water":
                        if state["water_available"] == True:
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
                    # crop = state["crops"].get(pos)
                    crop = crops_object["crops"].get(pos)
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
                    if not crop["is_planted"]:
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
                        # lines.append(f"- {pos}: needs_water = {info['needs_water']}")
                        lines.append(f"- {pos}: planted = {info['is_planted']}, needs_water = {info['needs_water']}")
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
                    crops = crops_object["crops"]
                    crop = crops.get((x, y))

                    new_x = state["player_pos"][0]
                    new_y = state["player_pos"][1]

                    is_correct_position = check_player_postion(
                        crops, new_x, new_y, x, y)

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

                    if crop["is_planted"]:
                        invalid_move_object["Already planted"] = invalid_move_object.get(
                            "Already planted", 0) + 1
                        invalid_moves += 1
                        return json.dumps({
                            "status": False,
                            "error": "Already planted",
                            "position": [x, y]
                        })

                    crop["is_planted"] = True

                    return json.dumps({
                        "status": True,
                        "action": "plant_crop",
                        "position": [x, y],
                        "planted": True
                    })

                # print(plant_crop(300,200))


                available_tools = {"move":move,"water":water,"collect_water":collect_water,"plant_crop":plant_crop}

                points_gained = 0
                points_gained_object = {}

                # you are smart farm game agent

                # Your task:
                # You have access to tools that let you move and interact with the world.
                # When the user gives a task, determine whether the task is already satisfied using the current world state.
                # sometimes the task can be ambigious and indirect.
                # If no task is provided, do nothing.
                # Only perform actions that are necessary to accomplish the user's requested task.
                # Think step-by-step.
                system_message2 = f"""
                Your task:
                You are a smart farm game agent. You have access to tools that let you move and interact with the world.

                User will communicate using direct commands or indirect statements. You must treat general statements and observations (e.g., "This land has so much potential" or "The crops look dry") as implicit tasks. Deduce the logical next action or required maintenance based on the statement.

                Before acting, determine whether the explicit or inferred task is already satisfied using the current world state. 

                If the user's statement is completely unrelated to the farm or game mechanics, do nothing. Otherwise, only perform actions that are necessary to accomplish the requested or inferred task.


                WORLD STATE:

                CURRENT STATE (authoritative):
                  
                Grid size: {state['grid_size']}
                Player position: {tuple(state['player_pos'])}
                  
                Crops to planted:
                {crops_to_text(crops_object['crops'])}

                Obstacles:
                {list(state['obstacles'])}

                Water_available:
                {state["water_available"]}
                Water_tank:
                {list(state['water_tank'])}


                move 25pxs and one side at a time
                

                call only one tool at a time.
 
                Tools available:
                {available_tools}

                """
                # new_content = " oh wheat crop is drying up"
                # new_content = "water the crops"
                # and not allowed to pass through the crop, water tank, they are obstacles.


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
                # model = model
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

                  new_crops = {}
                  i=0
                  while i< 50:
                      # time.sleep(1)
                      i+=1
                      st_time = time.time()    
                      # response: ChatResponse = client.chat(model=model, messages=messages, tools=[move,water,collect_water,plant_crop],think=True,options={"temperature": 0.0,"seed":42})
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
                        logger.info(f"content : {response.message.content}")
                      if response.message.thinking:
                        print('Thinking: ')
                        print(response.message.thinking + '\n')
                        logger.info(f"thinking : {response.message.thinking}")
                      messages.append(response.message)
                      
                      if response.message.tool_calls:
                        print("llm tool_calls:")
                        print(len(response.message.tool_calls))
                        for tool_call in response.message.tool_calls:
                          # time.sleep(1)
                          # LLM decides which function to call
                          function_to_call = available_tools.get(tool_call.function.name)
                          real_result_json = ""
                          if function_to_call:
                            try:
                                result = function_to_call(**tool_call.function.arguments)
                                print('Result from tool call name: ', tool_call.function.name, 'with arguments: ', tool_call.function.arguments, 'result: ', str(result) + '\n')
                                real_result_json = result
                            except Exception as e:
                                real_result_json = json.dumps({"status":"false", "message": f"Error in tool call: {str(e)}"})
                            logger.info(f"tool: {str(tool_call.function.name)}  result: {str(real_result_json)}") 
                            print(f"time for tool {tool_call.function.name}: {str(time.time()-st_time)}")
                            if "false" not in real_result_json:
                                tool_calls.append(tool_call.function.name)
                                time_taken.append(time.time()-st_time)
                            # time_taken.append(time.time()-st_time)
                            crops = crops_object["crops"]
                            new_crops = {}
                            j = 0
                            for k, v in crops.items():   
                                j += 1
                                new_crops[f"crop{j}"] = {
                                    "pos": list(k),
                                    "name": v["name"],
                                    "needs_water": v["needs_water"],
                                    "is_planted": v["is_planted"]
                                }
                            print(new_crops)
                            new_state = {
                                "grid_size": [800, 600],
                                "player_pos": state["player_pos"],
                                "crops": new_crops,
                                "obstacles": [250,100],
                                "water_available":state["water_available"],
                                "goal_completed": state["goal_completed"]
                            }
                            messages.append({
                              "role": "tool",
                              "content": json.dumps({
                                  "action_result": real_result_json,
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
                      elif goal_completed(state)==True:
                        print("goal completed:"+ str(state["goal_completed"]))
                        logger.info("goal completed")
                        break
                      # elif response.message.tool_calls == None:
                      #   print("LLm did not call the tools")
                      #   logger.error(f"LLm failed to call the tools: {str(e)}")
                      #   break
                      elif response.message.tool_calls == None and state["goal_completed"] == False:
                        print("LLM did not call tools but goal is not complete.")
                        print("goal completed state:"+str(state["goal_completed"]))
                        logger.info("goal completed state:"+str(state["goal_completed"]))
                        logger.info("LLm did not call tools but goal is not complete using replan")
                        messages.append({'role': 'user', 'content': "You did not select a tool. Please review your plan and select the next tool to execute."})
                        # Adding a fail-safe to prevent infinite loops if the model gets totally stuck
                        if len(messages) > 50: 
                             print("Message limit reached, aborting to prevent infinite loop.")
                             logger.error(f"Message limit reached, aborting to prevent infinite loop.")
                             break
                except Exception as e:
                  logger.error(f"LLm failed due to error: {str(e)}")
                  print(f"llm failed due to error: {e}")
                  # logger.info(log_messages)
                if state["water_available"] == True:
                    points_gained +=1
                    points_gained_object["water_available"] = 1

                reset_crop = {}
                j = 0
                crops = crops_object["crops"]
                for k,v in crops.items():
                    j+=1    
                    reset_crop[f"crop{j}"] = {"pos":list(k),"name":crops.get(k)["name"],"needs_water":True,"is_planted":False}
                    if crops.get(k)["is_planted"] == True:
                        points_gained_object[f"plant_crop_{j}"] = 1
                        points_gained+=1
                    if crops.get(k)["needs_water"] == False:
                        points_gained_object[f"needs_water_{j}"] = 1
                        points_gained+=1


                reset_state = {
                            "grid_size": [5, 5],
                            "player_pos": [200,100],

                            "crops": reset_crop,
                            "obstacles": [250,100],
                            "water_available":False,
                            "goal_completed": state["goal_completed"]
                        }

                response = requests.post(url, json=reset_state, headers=headers)
                final_score = 0
                print(time_taken)
                if len(time_taken)>0 and len(tool_calls) > 0:
                    final_score = find_final_score(time_taken,player_positions,points_gained_object,tool_calls,points_gained,revisits,state,invalid_moves,invalid_move_object,task_type)
                    print("final_score:")
                    print(final_score)

                else:
                    print("final_score:")
                    print(final_score)
                    # logger.info(log_messages)
                    logger.info("llm tool call failed") 
                    print("llm tool call failed")
                final_score_array.append(final_score)
                tool_calls_array.append(len(player_positions))
                result = []
                if len(tool_calls) >0:
                    result = [tool_calls[0]]
                    for action in tool_calls[1:]:
                        if action != result[-1]:
                            result.append(action)
                    print("tool_calls_after:")
                    print(result)
                tool_call_names.append(result)

            results[task_name][difficulty]["points"] = final_score_array
            results[task_name][difficulty]["tool_calls"] = tool_calls_array
            results[task_name][difficulty]["tool_names"] = tool_call_names


    final_result.append(results)
logger.info("final_result: "+str(final_result))
    # break

print(final_result)



