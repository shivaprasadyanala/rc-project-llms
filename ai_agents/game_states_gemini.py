states = {
    # # STATE 1: Basic Detour - A small vertical wall blocks the direct path to the crop.
    # "state1": {
    #     "grid_size": (800, 600),
    #     "player_pos": [100, 100], 
    #     "crops": {
    #         (200, 100): {"name": "rice", "planted": False, "needs_water": True}
    #     },
    #     "obstacles": [
    #         [150, 75], [150, 100], [150, 125] # Vertical wall
    #     ],
    #     "water_available": False,
    #     "water_tank": [75, 250],
    #     "goal_completed": False
    # },

    # # STATE 2: Cornering - An L-shaped wall forces the player to path around a corner to reach the crops.
    # "state2": {
    #     "grid_size": (800, 600),
    #     "player_pos": [100, 100], 
    #     "crops": {
    #         (250, 100): {"name": "rice", "planted": False, "needs_water": True},
    #         (250, 200): {"name": "wheat", "planted": False, "needs_water": True}
    #     },
    #     "obstacles": [
    #         [175, 75], [175, 100], [175, 125], [175, 150], # Vertical part of L
    #         [200, 150], [225, 150]                         # Horizontal part of L
    #     ],
    #     "water_available": False,
    #     "water_tank": [75, 250],
    #     "goal_completed": False
    # },

    # # STATE 3: The Chokepoint - A long wall divides the map. The player must find the single 25px gap to cross.
    # "state3": {
    #     "grid_size": (800, 600),
    #     "player_pos": [100, 150], 
    #     "crops": {
    #         (100, 250): {"name": "rice", "planted": False, "needs_water": True},
    #         (300, 100): {"name": "tomato", "planted": False, "needs_water": True},
    #         (300, 250): {"name": "wheat", "planted": False, "needs_water": True}
    #     },
    #     "obstacles": [
    #         [200, 50], [200, 75], [200, 100], [200, 125], [200, 150], # Top wall
    #         # GAP AT y=175
    #         [200, 200], [200, 225], [200, 250], [200, 275], [200, 300] # Bottom wall
    #     ],
    #     "water_available": False,
    #     "water_tank": [50, 50],
    #     "goal_completed": False
    # },

    # # STATE 4: The U-Trap & Guarded Water - Tests against greedy pathfinding. 
    # # Player must walk away from the target to get around the U-shape.
    # "state4": {
    #     "grid_size": (800, 600),
    #     "player_pos": [100, 150], 
    #     "crops": {
    #         (300, 150): {"name": "corn", "planted": False, "needs_water": True}, # Inside trap
    #         (400, 75): {"name": "rice", "planted": False, "needs_water": True},
    #         (400, 250): {"name": "tomato", "planted": False, "needs_water": True},
    #         (100, 300): {"name": "wheat", "planted": False, "needs_water": True}
    #     },
    #     "obstacles": [
    #         # U-Trap opening to the right
    #         [250, 100], [275, 100], [300, 100], [325, 100], # Top of U
    #         [250, 125], [250, 150], [250, 175],             # Back of U
    #         [250, 200], [275, 200], [300, 200], [325, 200], # Bottom of U
    #         # Guarding water tank
    #         [75, 200], [100, 200], [125, 200], [125, 225], [125, 250] 
    #     ],
    #     "water_available": False,
    #     "water_tank": [75, 250],
    #     "goal_completed": False
    # },

    # STATE 5: Zigzag Corridors - Forces serpentine movement and complex routing.
    # "state5": {
    #     "grid_size": (800, 600),
    #     "player_pos": [50, 50], 
    #     "crops": {
    #         (150, 150): {"name": "rice", "planted": False, "needs_water": True},
    #         (350, 50): {"name": "wheat", "planted": False, "needs_water": True},
    #         (350, 250): {"name": "tomato", "planted": False, "needs_water": True},
    #         (50, 350): {"name": "corn", "planted": False, "needs_water": True},
    #         (450, 150): {"name": "potato", "planted": False, "needs_water": True}
    #     },
    #     "obstacles": [
    #         # Wall 1 (Top-down)
    #         [100, 0], [100, 25], [100, 50], [100, 75], [100, 100], [100, 125], [100, 150], [100, 175],
    #         # Wall 2 (Bottom-up)
    #         [200, 100], [200, 125], [200, 150], [200, 175], [200, 200], [200, 225], [200, 250], [200, 275], [200, 300],
    #         # Wall 3 (Top-down)
    #         [300, 50], [300, 75], [300, 100], [300, 125], [300, 150], [300, 175], [300, 200],
    #         # Horizontal blocker
    #         [300, 200], [325, 200], [350, 200], [375, 200], [400, 200]
    #     ],
    #     "water_available": False,
    #     "water_tank": [50, 250],
    #     "goal_completed": False
    # },

    ## STATE 6: The Spiral Maze - Requires deep pathing, backtracking, and memory.
    "state6": {
        "grid_size": (800, 600),
        "player_pos": [50, 125], 
        "crops": {
            (225, 225): {"name": "rice", "planted": False, "needs_water": True},   # Deep inside the spiral
            (450, 50): {"name": "wheat", "planted": False, "needs_water": True},
            (450, 350): {"name": "tomato", "planted": False, "needs_water": True},
            (50, 350): {"name": "corn", "planted": False, "needs_water": True},
            (250, 400): {"name": "potato", "planted": False, "needs_water": True},
            (100, 100): {"name": "carrot", "planted": False, "needs_water": True}
        },
        "obstacles": [
            # OUTER RING (Entrance at [150, 125])
            # Top
            [150, 100], [175, 100], [200, 100], [225, 100], [250, 100], [275, 100], [300, 100], [325, 100], [350, 100],
            # Right
            [350, 125], [350, 150], [350, 175], [350, 200], [350, 225], [350, 250], [350, 275], [350, 300],
            # Bottom
            [150, 300], [175, 300], [200, 300], [225, 300], [250, 300], [275, 300], [300, 300], [325, 300],
            # Left
            [150, 150], [150, 175], [150, 200], [150, 225], [150, 250], [150, 275], # Notice [150, 125] is missing (the door)

            # INNER RING 1
            # Top
            [175, 150], [200, 150], [225, 150], [250, 150], [275, 150], [300, 150],
            # Right
            [300, 175], [300, 200], [300, 225], [300, 250],
            # Bottom
            [200, 250], [225, 250], [250, 250], [275, 250],
            # Left
            [200, 200], [200, 225],

            # INNER RING 2 (Core blocker)
            [225, 200], [250, 200]
        ],
        "water_available": False,
        "water_tank": [250, 225], # Trapped in the center of the spiral with the crop
        "goal_completed": False
    }
}