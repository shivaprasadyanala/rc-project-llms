"""
Tools for the ReAct agent.

This file defines individual tools. Import them in agent.py and add to the tools list there.
"""

import os
import random
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from langchain.tools import Tool
# import wikipedia

# from utils import make_request
import requests


def make_request(url, headers=None, timeout=10):
    """Helper function to make HTTP GET requests with error handling."""
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, str(e)

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




# Tool definitions - all Tool() instances are defined at the bottom
calculator_tool = Tool(
    name="calculator",
    func=calculator,
    description="Performs basic arithmetic calculations. Input should be a mathematical expression as a string (e.g., '2 + 2', '10 * 5', '100 / 4'). Use this tool when you need to perform mathematical calculations.",
)

random_int_tool = Tool(
    name="random_int",
    func=random_int,
    description="""Generates a random integer within a specified range. Input should be a range like "1-10" or "1,100" for min and max values. If no input is provided, defaults to 1-100. Use this tool when you need to generate a random integer.""",
)

geocode_tool = Tool(
    name="geocode",
    func=geocode,
    description="""Looks up latitude and longitude coordinates for a city name. Input should be a city name as a string (e.g., "Seattle", "New York", "Tokyo"). Returns the city's coordinates, country, and timezone. Use this tool when you need to find the geographic coordinates of a city. Note that the input should be only one city at a time and make sure that we do not add extra punctuation marks.""",
)

weather_tool = Tool(
    name="weather",
    func=weather,
    description="""Gets current weather information from weather.gov API. Input should be coordinates in the format "latitude, longitude" (e.g., "47.6062, -122.3321"). Returns temperature, forecast, and detailed weather information. Use this tool when you need weather information for specific coordinates.""",
)

time_tool = Tool(
    name="time",
    func=time,
    description="Gets the current time for a specific timezone. Input should be a timezone name (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo'). Returns the current time in that timezone in multiple formats. Use this tool when you need to know what time it is in a specific location.",
)

ls_tool = Tool(
    name="ls",
    func=ls,
    description="Lists all files in the files directory. No input required (any input is ignored). Returns a list of filenames in the directory. Use this tool when you want to see what files are available.",
)

read_tool = Tool(
    name="read",
    func=read,
    description="Reads the contents of a file from the files directory. Input should be a filename (e.g., 'notes.txt', 'data.json'). Only flat filenames are allowed - no paths or '..' sequences. Returns the complete file contents. Use this tool when you need to read a file.",
)

write_tool = Tool(
    name="write",
    func=write,
    description="Writes content to a file in the files directory. Input format must be 'filename|content' where the pipe character (|) separates the filename from the content. For example: 'notes.txt|Hello world'. Only flat filenames are allowed - no paths or '..' sequences. Creates or overwrites the file. Use this tool when you need to save data to a file.",
)

wikipedia_tool = Tool(
    name="wikipedia_tool",
    func=wikipedia_search,
    description="Searches Wikipedia for information on a given topic. Input should be a search query or topic name (e.g., 'Python programming', 'World War II', 'Isaac Newton'). Returns a summary from Wikipedia. Use this tool when you need to look up factual information or learn about a topic.",
)