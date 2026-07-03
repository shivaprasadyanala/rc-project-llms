from prompts.prompt_builder import build_prompt
import json
from pathlib import Path
from llm_tools import move,collect_water,plant_crop,water,state,invalid_moves,invalid_move_object
from ollama import Client
from ollama._types import ChatResponse
import requests
import time
from collections import Counter
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_path = LOG_DIR / "steps.jsonl"
client = Client(
   host="http://hal9000.skim.th-owl.de:11437",
    timeout=60  
)
model = 'gpt-oss:20b'

def log_step(record):
    with open(log_path, "a") as f:
        json.dump(record, f)
        f.write("\n")

combined_invalid_objects = Counter()

file_path = "./prompts/best_skill.md"
best_skill = ""
with open(file_path, "r", encoding="utf-8") as file:
    best_skill = file.read()

def update_best_skill(invalid_moves):
    prompt = """
    You are converting failure logs into concise behavioral rules for an agent skill file.

    Rules:
    - Be concrete and actionable
    - Avoid repetition
    - Do NOT restate failures
    - Output ONLY JSON list of strings


    Current Skill

    {best_skill}

    Common failures

    {invalid_moves}

    Suggest concrete additions or edits to the current skill.
    should follow th format of the current skill
    Do not rewrite unrelated sections."""
    messages = [
        {'role':'system','content':prompt},
    ]
    response: ChatResponse = client.chat(model=model, messages=messages, options={'temperature': 0.75})
    print("response:----")
    print(response.message.content)
    print("Thinking:----")
    print(response.message.thinking)

if log_path.exists():  
    with open(log_path, "r") as f:
        cnt = 0
        for line in f:
            line = line.strip()
            if not line:
                continue
            episode = json.loads(line)
            cnt+=1
            invalid_obj = episode.get("invalid_move_object", {})

            if isinstance(invalid_obj, dict):
                combined_invalid_objects.update(invalid_obj)
        if cnt == 10:
            update_best_skill(dict(combined_invalid_objects))
            pass
    print(dict(combined_invalid_objects))
else:
    print("No log file found yet.")

breakpoint()
available_tools = {"move":move,"water":water,"collect_water":collect_water,"plant_crop":plant_crop}

prompt = build_prompt(
    state=state,
    available_tools=available_tools,
)



# model = "llama3.1:8b"
# model = "qwen2.5:7b"
# model = "qwen3:8b"
# model = "ornith:9b"

# model = config_data["model"]["name"]
messages = [
{'role':'system','content':prompt},
 {'role': 'user', 'content': 'go to all crops and water them'}
 ]

new_crops = {}
player_positions = []
step = 0

url = "http://localhost:3000/post_game_state/"
headers = {
"Content-Type": "application/json"
}
tool_calls = []
reason_for_failure = "None"
while step< 80:
  # time.sleep(1)
  step+=1
  st_time = time.time()    
  response: ChatResponse = client.chat(model=model, messages=messages, tools=[move,water,collect_water,plant_crop], options={'temperature': 0.75})

  print("response::")
  print(response.message)
  # breakpoint()
  if response.message.content:
    print('Content: ')
    print(response.message.content + '\n')
    # log_messages.append(response.message.content)
  if response.message.thinking:
    print('Thinking: ')
    print(response.message.thinking + '\n')
    # log_messages.append(response.message.thinking)

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
        # log_messages.append({'role': 'tool', 'content': result, 'tool_name': tool_call.function.name})

        print(f"time for tool {tool_call.function.name}: {str(time.time()-st_time)}")
        tool_calls.append(tool_call.function.name)
        # time_taken.append(time.time()-st_time)
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
              "action_result": result,
              "current_state": new_state
          }),
          "tool_name": tool_call.function.name
      })

        print("new_state")
        print(new_state)
        player_positions.append(state["player_pos"])
        
        new_state["task"] = "test"
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
    # messages.append({'role': 'user', 'content': "You did not select a tool. Please review your plan and select the next tool to execute."})
    messages.append({'role': 'user', 'content': "The goal is not complete.Please review your plan and take appropriate action."})

    # Adding a fail-safe to prevent infinite loops if the model gets totally stuck
    if len(messages) > 150: 
        print("Message limit reached, aborting to prevent infinite loop.")
        reason_for_failure = "Message limit reached, aborting to prevent infinite loop."
        # logger.error(f"Message limit reached, aborting to prevent infinite loop.")
        break


# trajectory path also
# tool_calls_final = res = list(tool_calls)
result = [tool_calls[0]]
jumps = 0
threshold = 25
for i in range(len(player_positions) - 1):
    
    x1, y1 = player_positions[i]
    x2, y2 = player_positions[i + 1]

    if abs(x2 - x1) > threshold or abs(y2 - y1) > threshold:
        jumps +=1
        print(f"Jump > {threshold}px: {player_positions[i]} -> {player_positions[i+1]}")
print("game character jumps:"+ str(jumps))

invalid_moves+=jumps
if jumps > 0:
    invalid_move_object["moving more than 25px in one direction"] = invalid_move_object.get("moving more than 25px in one direction", 0) + jumps
# invalid_move_object
for action in tool_calls[1:]:
    if action != result[-1]:
        result.append(action)
tool_calls_final = result
log_object = {"total_steps":len(player_positions),"invalid moves":invalid_moves,"invalid_move_object":invalid_move_object,"trajectory":tool_calls_final,"goal_completed":state["goal_completed"],"task":"plant crop and water","reason_for_failure":reason_for_failure}

print(log_object)
log_step(log_object)


# Provide the current best_skill.md and a summary of failures.

# Example prompt:

# Current Skill

# <best_skill.md>

# Common failures

# - 38 episodes tried planting without water.
# - 21 revisited planted crops.
# - 17 ignored the closest water tank.

# Suggest concrete additions or edits to the skill document.
# Do not rewrite unrelated sections.


# if episodes_completed % 100 == 0:
#     failures = analyze_logs("logs/")
#     proposed_skill = propose_skill_update(
#         current_skill=load_skill(),
#         failures=failures
#     )

#     current_score = evaluate(load_skill())
#     proposed_score = evaluate(proposed_skill)

#     if proposed_score > current_score:
#         save_skill(proposed_skill)



# MAX_RETRIES = 5

# for i in range(MAX_RETRIES):
#     response = client.responses.create(
#         model="gpt-5.5",
#         input=prompt,
#         temperature=0.75,
#     )

#     plan = response.output_text

#     if is_valid(plan):
#         break

# def is_valid(plan):
#     return (
#         "collect_water" in plan and
#         "plant_crop" in plan
#     )