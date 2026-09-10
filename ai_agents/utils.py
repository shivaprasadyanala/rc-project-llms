from a_star_algo import astar
from my_logger import logger,config_data

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
    return True,matched_elements



correct_seq = []

def compute_similarity(list1, list2):
    common = len(set(list1) & set(list2))
    return common / len(list2) 

def find_optimal_path(state,task_type):
    starts = [[200,100],[75,250],[300,200],[200,100]]
    goals = [[75,250],[300,200],[400,275],[300,200]]
    obstacle = state["obstacles"]
    if task_type == "collect_water":
        return len(astar(starts[0],goals[0],obstacle))
    elif task_type == "plant_crop":
        return len(astar(starts[3],goals[3],obstacle)) + len(astar(starts[2],goals[2],obstacle))
    elif task_type == "plant_crop_water":
        return len(astar(starts[0],goals[0],obstacle)) + len(astar(starts[1],goals[1],obstacle))+len(astar(starts[2],goals[2],obstacle))

def find_final_score(time_taken,player_positions,points_gained_object,tool_calls,points_gained,revisits,state,invalid_moves,invalid_move_object,task_type):
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

    logger.info(f"time taken values: {time_taken}")


    if len(tool_calls)<=1:
        print(f"points gained by agent: 0")
        logger.info("points gained by agent: 0")
        return 0
    print(tool_calls)
    result = [tool_calls[0]]
    for action in tool_calls[1:]:
        if action != result[-1]:
            result.append(action)
    tool_calls_final = result
    print("--- Test sequence ---")
    actual_1 = tool_calls_final
    is_matched,matched_sequence = check_sequence_details(actual_1, correct_seq)
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

    obs = 0
    for pp in player_positions:
        if state["obstacles"][0] == pp:
            obs += 1 
    invalid_moves+=obs
    print("game character jumps:"+ str(jumps))
    logger.info("game character jumps:"+ str(jumps))
    invalid_moves+=jumps
    invalid_move_rate = 1
    if invalid_moves <= len(player_positions):
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
    revisit_rate = revisits/len(player_positions)
    logger.info("no of revisits:"+ str(revisits))
    success_rate = 0
    if points_gained > 0:
        success_rate = 1
    print("success_rate:")
    print(success_rate)

    a1 = list(set(tool_calls_final))
    a2 = []
    max_task_points = 0
    if task_type == "collect_water":
        a2 = ['move', 'collect_water']
        max_task_points = 1
    elif task_type == "plant_crop":
        a2 = ['move', 'plant_crop']
        max_task_points = 2
    elif task_type == "plant_crop_water":
        a2 = ['move', 'collect_water','plant_crop','water']
        max_task_points = 5

    tool_call_accuracy = compute_similarity(a1.copy(),a2.copy())
    print("tool tool_call_accuracy:")
    print(tool_call_accuracy)
    print(a1,a2)

    optimal_path_length = find_optimal_path(state,task_type)
    print("optimal_path_length:")
    print(optimal_path_length)

    nav_efficiency = len(player_positions)/optimal_path_length
    new_nav_efficieny = nav_efficiency
    if nav_efficiency > 1:
        new_nav_efficieny = 1 / nav_efficiency
    print("navigation efficiency:")
    print(new_nav_efficieny)
    task_score_rate = 0
    if points_gained > max_task_points:
        if state["goal_completed"] == True:
            # task_score_rate = 1
            task_score_rate = max_task_points/points_gained
    else:
        task_score_rate = points_gained/max_task_points
        print("task score rate:")

    scoring_type = config_data["scoring"]["type"]
    if scoring_type == "trajectory":
        final_score =  (0.50 * task_score_rate) + (0.20 * tool_call_accuracy) + (0.15 * new_nav_efficieny) + (0.10 * (1 - invalid_move_rate)) + (0.05 * (1 - revisit_rate))
    else:
        return points_gained

    # final_score =  task_score_rate *((0.5 * tool_call_accuracy) + (0.2 * nav_efficiency) + (0.2 * (1 - invalid_move_rate)) + (0.1 * (1 - revisit_rate)))
    return final_score
