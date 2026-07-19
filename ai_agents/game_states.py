states = {
"state1": {
    "grid_size": (800, 600),
    "player_pos": [200, 100], 
    "crops": {
        (300, 200): {"name":"rice","planted":False,"needs_water": True}
    },
    "obstacles": [[350, 100],[150, 100],[250, 50]],
    "water_available":False,
    "water_tank":[75,250],
    "goal_completed": False
},

"state2":{
    "grid_size": (800, 600),
    "player_pos": [200, 100], 
    "crops": {
        (300, 250): {"name":"rice","planted":False,"needs_water": True},
        (125, 50): {"name":"wheat","planted":False,"needs_water": True}
    },
    "obstacles": [[150, 200],[350, 25],[300, 100],[250, 200],[250, 100]],
    "water_available": False,
    "water_tank":[75,250],
    "goal_completed": False
},

"state3":{
    "grid_size": (800, 600),
    "player_pos": [200, 100], 
    "crops": {
        (300, 200): {"name":"rice","planted":False,"needs_water": True},
        (125, 50): {"name":"tomato","planted":False,"needs_water": True},
        (225, 150): {"name":"wheat","planted":False,"needs_water": True}
    },
    "obstacles": [[250, 25],[250, 125],[225, 150],[100, 50],[150, 70],[25, 50],[50, 200]],
    "water_available": False,
    "water_tank":[75,250],
    "goal_completed": False
}

}