
state = {
    "grid_size": (800, 600),

    # Player
    "player_pos": [200, 100],  # use list for mutability

    # Crops indexed by position
    "crops": {
        (400, 275): {"name":"wheat","planted":False,"needs_water": True},
        (300, 200): {"name":"rice","planted":False,"needs_water": True},
        (200,475): {"name":"sugarcane","planted":False,"needs_water": True},
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
    print("value of goal completed:" + str(value))
    if value ==3:
        state["goal_completed"]= True
    return state["goal_completed"]



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
