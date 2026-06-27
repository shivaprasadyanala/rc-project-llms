"""
Tools for the ReAct agent.

This file defines individual tools. Import them in agent.py and add to the tools list there.
"""

import os
import random
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from langchain.tools import tool
# import wikipedia
import json
import requests
# from utils import make_request

# Base directory for file operations
FILES_DIR = Path(__file__).parent / "files"


def _validate_and_get_file_path(filename: str = None) -> Path:
    """Validate filename and return the full path within FILES_DIR.
    
    Args:
        filename: Optional filename to validate. If None, just ensures directory exists.
    
    Returns:
        Path object for the file or FILES_DIR if no filename provided.
    
    Raises:
        ValueError: If filename contains invalid characters for security.
    """
    # Create files directory if it doesn't exist
    FILES_DIR.mkdir(exist_ok=True)
    
    if filename is None:
        return FILES_DIR
    
    # Security check: prevent directory traversal
    if "../" in filename or ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename. Only flat filenames are allowed (no paths or '..')")
    
    return FILES_DIR / filename


def calculator(expression: str) -> str:
    print("\n🔢 Calculator tool running...\n")
    try:
        # Evaluate the expression
        result = eval(expression)
        return f"The result of {expression} is {result}\n"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}\n"


def random_int(range_str: str = "1-100") -> str:
    print("\n🎲 Random int tool running...\n")
    try:
        # Support both "1-10" and "1,10" formats
        if '-' in range_str:
            min_val, max_val = range_str.split('-')
        elif ',' in range_str:
            min_val, max_val = range_str.split(',')
        else:
            return "Error: Please use format like '1-10' or '1,100'\n"

        min_val = int(min_val.strip())
        max_val = int(max_val.strip())

        result = random.randint(min_val, max_val)
        return f"Random integer between {min_val} and {max_val}: {result}\n"
    except Exception as e:
        return f"Error generating random integer: {str(e)}\n"


def geocode(city_name: str) -> str:
    """Look up latitude/longitude for a city."""
    print(f"\n🌍 Geocode tool running...\n")
    print(f"[TOOL] Executing geocode with parameters: city_name='{city_name}'")
    
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
    success, data = make_request(url)
    
    if not success:
        return f"Error: {data}\n"
    
    if "results" in data and len(data["results"]) > 0:
        result = data["results"][0]
        return f"City: {result['name']}, {result.get('country', '')}\nLatitude: {result['latitude']}\nLongitude: {result['longitude']}\nTimezone: {result.get('timezone', '')}\n"
    else:
        return f"Error: City '{city_name}' not found\n"


def weather(coordinates: str) -> str:
    """Get weather information from weather.gov API.
    
    Args:
        coordinates: String in format "latitude, longitude"
    
    Example API call:
    curl -L -H "User-Agent: ReActAgent/1.0" "https://api.weather.gov/points/47.6062,-122.3321"
        Given properties->forecast, curl that URL for the forecast data
    """
    print(f"\n🌤️  Weather tool running...\n")
    print(f"[TOOL] Executing weather with parameters: coordinates='{coordinates}'")
    
    # Parse the coordinates string
    parts = coordinates.split(',')
    try:
        latitude = float(parts[0].strip())
        longitude = float(parts[1].strip())
    except (ValueError, IndexError):
        return "Error: Invalid latitude/longitude values\n"
    
    # Step 1: Get the forecast URL from the points endpoint
    url = f"https://api.weather.gov/points/{latitude},{longitude}"
    headers = {"User-Agent": "ReActAgent/1.0"}
    success, data = make_request(url, headers=headers)
    
    if not success:
        return f"Error: {data}\n"
    
    # Step 2: Get the forecast from the forecast URL
    forecast_url = data["properties"]["forecast"]
    success, forecast_data = make_request(forecast_url, headers=headers)
    
    if not success:
        return f"Error: {forecast_data}\n"
    
    # Get first period (current/upcoming)
    if forecast_data["properties"]["periods"]:
        period = forecast_data["properties"]["periods"][0]
        return f"{period['name']}: {period['temperature']}°{period['temperatureUnit']}\n{period['shortForecast']}\n{period['detailedForecast']}\n"
    
    return "Error: No forecast data available\n"


def time(timezone: str) -> str:
    """Get current time for a timezone.
    
    Note: This is computed locally using Python's datetime and zoneinfo,
    not via an external API call.
    """
    print(f"\n🕐 Time tool running...\n")
    print(f"[TOOL] Executing time with parameters: timezone='{timezone}'")
    try:
        tz = ZoneInfo(timezone)
        current_time = datetime.now(tz)
        return f"Timezone: {timezone}\nTime: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\nFormatted: {current_time.strftime('%I:%M %p')}\n"
    except Exception as e:
        return f"Error: {str(e)}\n"


def ls(unused: str = "") -> str:
    """List files in the files directory."""
    print(f"\n📂 List files tool running...\n")
    print(f"[TOOL] Executing ls")
    
    try:
        files_dir = _validate_and_get_file_path()
        files = [f.name for f in files_dir.iterdir() if f.is_file()]
        if files:
            return f"Files in directory:\n" + "\n".join(f"  - {f}" for f in sorted(files)) + "\n"
        else:
            return "Directory is empty\n"
    except Exception as e:
        return f"Error listing files: {str(e)}\n"


def read(filename: str) -> str:
    """Read a file from the files directory."""
    print(f"\n📖 Read file tool running...\n")
    print(f"[TOOL] Executing read with parameters: filename='{filename}'")
    
    try:
        file_path = _validate_and_get_file_path(filename)
        
        if not file_path.exists():
            return f"Error: File '{filename}' does not exist\n"
        
        content = file_path.read_text()
        return f"Contents of '{filename}':\n{content}\n"
    except Exception as e:
        return f"Error reading file: {str(e)}\n"


def write(input_str: str) -> str:
    """Write content to a file in the files directory.

    Input format: "filename|content" where | is the separator.
    """
    print(f"\n✍️  Write file tool running...\n")
    print(f"[TOOL] Executing write")

    try:
        # Parse input
        if "|" not in input_str:
            return "Error: Input must be in format 'filename|content'\n"

        parts = input_str.split("|", 1)
        filename = parts[0].strip()
        content = parts[1] if len(parts) > 1 else ""

        file_path = _validate_and_get_file_path(filename)
        file_path.write_text(content)
        return f"Successfully wrote {len(content)} characters to '{filename}'\n"
    except Exception as e:
        return f"Error writing file: {str(e)}\n"


def wikipedia_search(query: str) -> str:
    """Search Wikipedia for information on a given topic."""
    print(f"\n📖 Wikipedia tool running...\n")
    print(f"[TOOL] Executing wikipedia_search with parameters: query='{query}'")

    try:
        summary = wikipedia.summary(query)
        return f"Wikipedia summary for '{query}':\n{summary}\n"
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found for '{query}'. Please be more specific. Some options: {', '.join(e.options[:5])}\n"
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'\n"
    except Exception as e:
        return f"Error querying Wikipedia: {str(e)}\n"

import heapq
from langchain.tools import Tool,tool
import json
TILE_SIZE = 25

state = {
    "grid_size": (800, 600),
    "player_pos": [200, 100],  # use list for mutability
    "crops": {
        (400, 275): {"name":"wheat","planted":False,"needs_water": True},
        (300, 200): {"name":"rice","planted":False,"needs_water": True},
        # (200,475): {"name":"sugarcane","planted":False,"needs_water": True},
        },
    "obstacles": {(250, 100)},
    "water_available":False,
    "water_tank":{(75,250)},
    "goal_completed": False
}
points = 0
points_object = {"points":0}


def to_grid(pos):
    return (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)

def to_pixel(pos):
    return (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE)

def heuristic(a, b):
    # Manhattan distance
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

@tool
def astar(json_input: str)->str:
    """
        a star algorithm which takes the start pixal, goal fixal, obstacle pixal, grid width, and gird height
        to calculate the path from the starting point to the goal by dodging the obstacles.
        Args:
          start_px int,int: x,y coordinates of start
          goal_px int,int: x,y coordinate of goal
          obstacles_px [(int,int)] : x,y coordinate of obstacles
      Returns:
        List: The list of tuples of the player coordinates to reach the destination
    
        A sample input for the function
        start_px = (50,75)
        goal_px = (150,125)

        obstacles = [
            (75, 75),
        (100, 75),
        (125, 75)
    ]
    
    """
    # print(type(start_px))
    # print((start_px))
    # print((goal_px))
    # print(obstacles_px)
    
    # try:
    grid_width=800
    grid_height=600
    args = json.loads(json_input)
    # 2. Convert lists back to tuples for your game engine
    start_px = tuple(args["start_px"])
    goal_px = tuple(args["goal_px"])
    obstacles_px = [tuple(obs) for obs in args["obstacles_px"]]


    new_st = (int(start_px[0]),int(start_px[1]))
    new_goal = ( int(goal_px[0]),int(goal_px[1]))
    # print(new_goal)
    # print(new_st)
    start = to_grid(new_st)
    goal = to_grid(new_goal)
   
    obstacles =[]
    for obstacle in obstacles_px:
        obstacle_tuple = (obstacle[0],obstacle[1])
        obstacles.append(to_grid(obstacle_tuple))

    # print(obstacles)
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            # reconstruct path
            path = []
            while current in came_from:
                path.append(to_pixel(current))
                current = came_from[current]
            path.append(to_pixel(start))
            path.reverse()
            return f"path from start to destination is: {path}"
            # return path

        x, y = current

        neighbors = [
            (x+1, y),
            (x-1, y),
            (x, y+1),
            (x, y-1),
        ]

        for nx, ny in neighbors:
            neighbor = (nx, ny)

            # bounds check
            if nx < 0 or ny < 0 or nx >= int(grid_width) or ny >= int(grid_height):
                continue

            # obstacle check
            if neighbor in obstacles:
                continue

            tentative_g = g_score[current] + 1

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    return None  # no path found
    # except Exception as e:
    #     return "pass correct argument to the tool."




def crops_to_text(crops):
    lines = []
    for pos, info in crops.items():
      lines.append(f"- {pos}: needs_water = {info['needs_water']}")
    return "\n".join(lines)

nstate =  f"""CURRENT STATE (authoritative):
  
Grid size: {state['grid_size']}
Player position: {tuple(state['player_pos'])}
  
Crops:
{crops_to_text(state['crops'])}

Obstacles:
{list(state['obstacles'])}

Water_available:
{state["water_available"]}
Water_tank:
{list(state['water_tank'])}"""

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


# set_crop_state()
# breakpoint()
@tool
def water()-> str:
    """
      waters the crop and changes the state accordingly
      CRITICAL: You CANNOT use this tool unless the crop at the current location 
      has already been planted using the plant_crop_tool.
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
    points_object["points"]+=1
    crop = state["crops"].get(pos)
    print(crop)
    if not crop:
        return "ACTION FAILED: There is no crop planted here. You must use the plant_crop tool first."

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
    update_phaser_game_state()
    return json.dumps({
        "status":"true",
        "action":"water",
        "message": "crop watered successfully"
        })

@tool
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
    points_object["points"]+=1
    update_phaser_game_state()
    return json.dumps({
        "status":"true",
        "action":"collect water",
        "water_available": state["water_available"]
    })
headers = {
"Content-Type": "application/json"
}
crops = state["crops"]

new_crops = {}
def update_phaser_game_state():
    i = 0
    for k,v in crops.items():   
        i+=1
        if crops.get(k) != None:
            if state["player_pos"] == list(k):
                new_crops[f"crop{i}"] = {"pos":list(k),"name":crops.get(tuple(state["player_pos"]))["name"],"needs_water":crops.get(tuple(state["player_pos"]))["needs_water"],"planted":crops.get(tuple(state["player_pos"]))["planted"]}
    new_state = {
      "grid_size": [5, 5],
      "player_pos": state["player_pos"],
      "crops": new_crops,
      "obstacles": [250,100],
      "water_available":state["water_available"],
      "goal_completed": state["goal_completed"]
    }
    new_state["task"] = "testing....."
    new_task_state = new_state
    url = "http://localhost:3000/post_game_state/"
    response = requests.post(url, json=new_task_state, headers=headers)
moves = []

@tool
def move(json_input: str)-> str:
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
    args = json.loads(json_input)
    dx = args["dx"]
    dy = args["dy"]
    new_x = state["player_pos"][0] + int(dx)
    new_y = state["player_pos"][1] + int(dy)
    moves.append([state["player_pos"][0],state["player_pos"][1]])

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
    update_phaser_game_state()
    return f"\n Observation: Moved successfully. New position is {state['player_pos']}. Continue following the astar path."
    # return json.dumps({
    #     "status":"true",
    #     "action":"move",
    #     "player_pos": state["player_pos"]
    # })

@tool
def plant_crop(json_input: str)-> str:
    """
    Plant a crop at the given grid coordinate (x,y).
    USE THIS FIRST. Plants a seed at the current location.
    You MUST use this tool before you can use the water_tool.
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
    args = json.loads(json_input)
    x = args["x"]
    y = args["y"]
    crop = state["crops"].get((x, y))
    points_object["points"]+=1
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
    update_phaser_game_state()
    return json.dumps({
        "status": True,
        "action": "plant_crop",
        "position": [x, y],
        "planted": True
    })
@tool
def follow_path(path_input: str) -> str:
    """
    Moves the agent along a sequence of coordinates to reach a destination.
    Action Input MUST be a valid JSON string containing the 'path' as a list of [x, y] coordinates.
    Example: {"path": [[200, 100], [200, 125], [175, 125]]}
    """
    try:
        # 1. Parse the JSON string from the LLM
        args = json.loads(path_input)
        path = args.get("path")
        
        if not path or not isinstance(path, list):
            return "Error: You must provide a valid 'path' array."

        # 2. Iterate through the path behind the scenes (The While/For Loop)
        for step in path:
            # Convert list back to tuple for your game state (e.g., [200, 100] -> (200, 100))
            current_x, current_y = step[0], step[1]
            
            # --- INSERT YOUR INTERNAL GAME LOGIC HERE ---
            # Update your nstate or call your game engine's move function directly.
            # Example: 
            # engine.move_sprite(current_x, current_y)
            # nstate["player_pos"] = (current_x, current_y)
            
            # (Optional) You can add a time.sleep(0.1) here if you want to watch 
            # the sprite move visually on your screen while the tool runs!
            # ------------------------------------------

        # 3. Return the single success observation to the LLM
        final_pos = path[-1]
        return f"Successfully arrived at destination {final_pos}. What is the next task?"

    except json.JSONDecodeError:
        return "Error: Action Input was not valid JSON. Please format as {\"path\": [[x, y], ...]}"
    except Exception as e:
        return f"Error executing follow_path: {str(e)}"

# Tool definitions - all Tool() instances are defined at the bottom
# plant_crop_tool = Tool(
#     name="plant_crop",
#     func=plant_crop,
#     description="plants the crop on the field and changes the global state of game",
# )

# move_tool = Tool(
#     name="move",
#     func=move,
#     description="performs move action by taking dx and dy coordinates of the player character and updating the game state.",
# )
# collect_water_tool = Tool(
#     name="collect water ",
#     func=collect_water,
#     description="Performs collecting water opeation at the water tank and updateing the game state",
# )

# water_tool = Tool(
#     name="water",
#     func=water,
#     description="Performs watering opeation for a crop and updating the game state accordingly",
# )
# astar_tool = Tool(
#     name="astar",
#     func=astar,
#     description="finds the shortest path to the target object on the field and updating the game state accordingly",
# )

# calculator_tool = Tool(
#     name="calculator",
#     func=calculator,
#     description="Performs basic arithmetic calculations. Input should be a mathematical expression as a string (e.g., '2 + 2', '10 * 5', '100 / 4'). Use this tool when you need to perform mathematical calculations.",
# )
# calculator_tool = Tool(
#     name="calculator",
#     func=calculator,
#     description="Performs basic arithmetic calculations. Input should be a mathematical expression as a string (e.g., '2 + 2', '10 * 5', '100 / 4'). Use this tool when you need to perform mathematical calculations.",
# )

# random_int_tool = Tool(
#     name="random_int",
#     func=random_int,
#     description="""Generates a random integer within a specified range. Input should be a range like "1-10" or "1,100" for min and max values. If no input is provided, defaults to 1-100. Use this tool when you need to generate a random integer.""",
# )

# geocode_tool = Tool(
#     name="geocode",
#     func=geocode,
#     description="""Looks up latitude and longitude coordinates for a city name. Input should be a city name as a string (e.g., "Seattle", "New York", "Tokyo"). Returns the city's coordinates, country, and timezone. Use this tool when you need to find the geographic coordinates of a city. Note that the input should be only one city at a time and make sure that we do not add extra punctuation marks.""",
# )

# weather_tool = Tool(
#     name="weather",
#     func=weather,
#     description="""Gets current weather information from weather.gov API. Input should be coordinates in the format "latitude, longitude" (e.g., "47.6062, -122.3321"). Returns temperature, forecast, and detailed weather information. Use this tool when you need weather information for specific coordinates.""",
# )

# time_tool = Tool(
#     name="time",
#     func=time,
#     description="Gets the current time for a specific timezone. Input should be a timezone name (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo'). Returns the current time in that timezone in multiple formats. Use this tool when you need to know what time it is in a specific location.",
# )

# ls_tool = Tool(
#     name="ls",
#     func=ls,
#     description="Lists all files in the files directory. No input required (any input is ignored). Returns a list of filenames in the directory. Use this tool when you want to see what files are available.",
# )

# read_tool = Tool(
#     name="read",
#     func=read,
#     description="Reads the contents of a file from the files directory. Input should be a filename (e.g., 'notes.txt', 'data.json'). Only flat filenames are allowed - no paths or '..' sequences. Returns the complete file contents. Use this tool when you need to read a file.",
# )

# write_tool = Tool(
#     name="write",
#     func=write,
#     description="Writes content to a file in the files directory. Input format must be 'filename|content' where the pipe character (|) separates the filename from the content. For example: 'notes.txt|Hello world'. Only flat filenames are allowed - no paths or '..' sequences. Creates or overwrites the file. Use this tool when you need to save data to a file.",
# )

# wikipedia_tool = Tool(
#     name="wikipedia_tool",
#     func=wikipedia_search,
#     description="Searches Wikipedia for information on a given topic. Input should be a search query or topic name (e.g., 'Python programming', 'World War II', 'Isaac Newton'). Returns a summary from Wikipedia. Use this tool when you need to look up factual information or learn about a topic.",
# )