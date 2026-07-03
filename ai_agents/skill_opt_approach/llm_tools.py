import json

invalid_moves = 0
revisits = 0
visited = set()
invalid_move_object = {}

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

def water()-> str:
    try:
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
            invalid_move_object["watering where there is not crop"] = invalid_move_object.get("watering where there is not crop", 0) + 1
            return {
            "status":"false",
            "action":"water",
            "message": "no crop here"
            }
        if not crop["planted"]:
            invalid_moves+=1
            invalid_move_object["watering before the crop is planted"] = invalid_move_object.get("watering before the crop is planted", 0) + 1
            return {
            "status":"false",
            "action":"water",
            "message": "crop not planted"
            }

        if not crop["needs_water"]:
            invalid_moves+=1
            # return "Crop already watered"
            invalid_move_object["watering the already watered crop"] = invalid_move_object.get("watering the already watered crop", 0) + 1
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
    except Exception as e:
        print(e)
        invalid_move_object["invalid tool arguments"] = invalid_move_object.get("invalid tool arguments", 0) + 1


def collect_water()-> str:
    try:
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
            invalid_move_object["collecting the water at wrong postion"] = invalid_move_object.get("collecting the water at wrong postion", 0) + 1
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
    except Exception as e:
        print(e)
        invalid_move_object["invalid tool arguments"] = invalid_move_object.get("invalid tool arguments", 0) + 1




def crops_to_text(crops):
    lines = []
    for pos, info in crops.items():
      lines.append(f"- {pos}: needs_water = {info['needs_water']}")
    return "\n".join(lines)

def move(dx:int, dy:int)-> str:
    try:
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
            invalid_move_object["diagonal_move is not allowed"] = invalid_move_object.get("diagonal_move not allowed", 0) + 1
            return json.dumps({
            "status":"false",
            "action":"move",
            "player_pos": state["player_pos"],
            "error":"diagonal move not allowed"
            })

        VALID_PAIRS = {(0, -25), (0, 25), (-25, 0),(25, 0)}
        if (dx,dy) not in VALID_PAIRS:
            invalid_moves+=1
            invalid_move_object["tool argument values are not 25px"] = invalid_move_object.get("tool argument values are not 25px", 0) + 1
            return json.dumps({
            "status":"false",
            "action":"move",
            "player_pos": state["player_pos"],
            "error":"invalid tool argument values check the rules again."
            })

        if not (0 <= new_x < state["grid_size"][0] and
                0 <= new_y < state["grid_size"][1]):
            invalid_moves+=1
            invalid_move_object["moving out of bounds"] = invalid_move_object.get("moving out of bounds", 0) + 1

            return json.dumps({
            "status":"false",
            "action":"move",
            "player_pos": state["player_pos"],
            "error":"Blocked: out of bounds"
            })

        # Obstacle check
        if (new_x, new_y) in state["obstacles"]:
            invalid_moves+=1
            invalid_move_object["crossing the blocked obstacle"] = invalid_move_object.get("crossing the blocked obstacle", 0) + 1
            return json.dumps({
            "status":"false",
            "action":"move",
            "player_pos": state["player_pos"],
            "error":"Blocked: obstacle"
            })
        if (new_x, new_y) in visited:
            revisits+=1
            state["player_pos"] = [new_x, new_y]
            invalid_move_object["visiting the already visited position"] = invalid_move_object.get("visiting the already visited position", 0) + 1
            return json.dumps({
                "status":"true",
                "action":"move",
                "player_pos": state["player_pos"],
                "error":"already visited"
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
    except Exception as e:
        print(e)
        invalid_move_object["invalid tool arguments"] = invalid_move_object.get("invalid tool arguments", 0) + 1


def plant_crop(x:int, y:int)-> str:
    try:
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
        # checking if there a crop object in the state
        if not crop:
            invalid_moves+=1
            invalid_move_object["No crop here"] = invalid_move_object.get("No crop here", 0) + 1
            return json.dumps({
                "status": False,
                "error": "No crop here",
                "position": [x, y]
            })

        if crop["planted"]:
            invalid_move_object["planting at a already cropped poistion"] = invalid_move_object.get("planting at a already cropped poistion", 0) + 1
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
    except Exception as e:
        print(e)
        invalid_move_object["invalid tool arguments"] = invalid_move_object.get("invalid tool arguments", 0) + 1