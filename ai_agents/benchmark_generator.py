import json
import random





import json

# Open and read the JSON file
# processed_data = []
# with open('game_states.json', 'r') as file:
#     # Parse the JSON file into a Python dictionary
#     data = json.load(file)
#     # print(data)
#     for dat in data:
#         crops = dat["crops"]
#         processed_crops = {
#             tuple(map(int, key.split(','))): value 
#             for key, value in crops.items()
#         }
#         dat["crops"] = processed_crops
#         processed_data.append(dat)

# breakpoint()





def get_valid_coord():
    """Generates a coordinate (x, y) that is a multiple of 25 and <= 400."""
    x = random.randint(0, 16) * 25
    y = random.randint(0, 16) * 25
    return x, y

def generate_game_states(num_objects=50, filename='game_states.json'):
    data_list = []
    
    # Possible random values for variety
    crop_names = ["wheat", "rice", "corn", "potato","sugarcane","tomato"]
    goals = ["plant rice crop", "water wheat crop", "collect water", "plant nearest crop"]

    for _ in range(num_objects):
        # Generate 5 unique coordinates to prevent entities from spawning on top of each other
        unique_coords = set()
        while len(unique_coords) < 5:
            unique_coords.add(get_valid_coord())
        
        coords = list(unique_coords)
        
        player_pos = list(coords[0])
        crop1_pos = coords[1]
        crop2_pos = coords[2]
        obstacle_pos = list(coords[3])
        water_tank_pos = list(coords[4])

        # Construct the valid JSON object
        game_state = {
            "grid_size": [800, 600],
            "player_pos": player_pos,
            "crops": {
                # Tuple keys converted to strings for valid JSON
                f"{crop1_pos[0]},{crop1_pos[1]}": {
                    "name": random.choice(crop_names),
                    "planted": random.choice([True, False]),
                    "needs_water": random.choice([True, False])
                },
                f"{crop2_pos[0]},{crop2_pos[1]}": {
                    "name": random.choice(crop_names),
                    "planted": random.choice([True, False]),
                    "needs_water": random.choice([True, False])
                }
            },
            # Sets converted to list of lists for valid JSON
            "obstacles": [obstacle_pos],
            "goal": random.choice(goals),
            "water_available": random.choice([True, False]),
            "water_tank": water_tank_pos,
            "goal_completed": False
        }
        
        data_list.append(game_state)

    # Save to a JSON file
    with open(filename, 'w') as json_file:
        json.dump(data_list, json_file, indent=4)
        
    print(f"Successfully generated {num_objects} objects and saved to '{filename}'.")

if __name__ == "__main__":
    generate_game_states()



