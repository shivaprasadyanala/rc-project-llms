from typing import Dict, Any
import json
from ollama import Client
import requests

reasoning_client = Client(
     "http://hal9000.skim.th-owl.de:11437",
)

tool_client = Client(
    "http://hal9000.skim.th-owl.de:11437",
)
# ----------------------------
# TOOLS
# ----------------------------

def get_weather(city: str) -> Dict[str, Any]:
    # Real implementation would call an API
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"

    geo_response = requests.get(
        geo_url,
        params={
            "name": city,
            "count": 1
        },
        timeout=10
    )

    geo_response.raise_for_status()

    geo_data = geo_response.json()

    if not geo_data.get("results"):
        raise ValueError(f"City not found: {city}")

    location = geo_data["results"][0]

    lat = location["latitude"]
    lon = location["longitude"]

    # Step 2: Fetch weather
    weather_url = "https://api.open-meteo.com/v1/forecast"

    weather_response = requests.get(
        weather_url,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "weather_code"
            ]
        },
        timeout=10
    )

    weather_response.raise_for_status()

    weather_data = weather_response.json()

    current = weather_data["current"]

    # Open-Meteo weather code mapping
    weather_codes = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing Rime Fog",
        51: "Light Drizzle",
        61: "Light Rain",
        63: "Rain",
        65: "Heavy Rain",
        71: "Snow",
        80: "Rain Showers",
        95: "Thunderstorm"
    }

    return {
        "city": location["name"],
        "country": location.get("country"),
        "temperature": current["temperature_2m"],
        "condition": weather_codes.get(
            current["weather_code"],
            "Unknown"
        )
    }


TOOLS = {
    "get_weather": get_weather
}



# ----------------------------
# REASONING MODEL
# ----------------------------

class ReasoningAgent:
    def create_plan(self, user_query):

        response = reasoning_client.chat(
            model="gpt-oss:20b",
            messages=[
                 {
                "role": "system",
                "content": """
                Create a tool plan.

                Return JSON only.

                Example:
                {
                  "steps": [
                    {
                      "tool": "get_weather",
                      "args": {
                        "city": "Berlin"
                      }
                    }
                  ]
                }
                """
            },
                {
                    "role": "user",
                    "content": user_query
                }
            ]
        )
        print(response)
        # return response.message.content
        return json.loads(
            response.message.content
        )

    def synthesize(self,user_query,tool_results):

        response = reasoning_client.chat(
            model="gpt-oss:20b",
            messages=[
                {
                    "role": "system",
                    "content": "Answer using tool results."
                },
                {
                    "role": "user",
                    "content": f"""
                    Question:
                    {user_query}

                    Tool Results:
                    {json.dumps(tool_results)}
                    """
                }
            ]
        )

        return response.message.content


# ----------------------------
# TOOL-CALLING MODEL
# ----------------------------

class ToolAgent:

    def execute_step(self, step):
        # “Decide whether a tool should be called, and if yes, how to fill its arguments.”
        response = tool_client.chat(
            model="qwen3:8b",
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(step)
                }
            ],
            tools=[get_weather
                # {
                #     "type": "function",
                #     "function": {
                #         "name": "get_weather",
                #         "parameters": {
                #             "type": "object",
                #             "properties": {
                #                 "city": {"type": "string"}
                #             },
                #             "required": ["city"]
                #         }
                #     }
                # }
            ]
        )

        tool_call = response.message.tool_calls[0]
        print(tool_call.function.arguments)
        return TOOLS[tool_call.function.name](
            **(tool_call.function.arguments)
        )


# ----------------------------
# ORCHESTRATOR
# ----------------------------

class AgentSystem:

    def __init__(self):
        self.reasoner = ReasoningAgent()
        self.tool_agent = ToolAgent()

    def run(self, user_query: str):

        # Step 1: Reasoning model creates plan
        plan = self.reasoner.create_plan(user_query)

        print("PLAN")
        print(json.dumps(plan, indent=2))
        print(type(plan))
        # Step 2: Tool model executes plan
        tool_results = []

        for step in plan["steps"]:
            result = self.tool_agent.execute_step(step)
            print(result)
            tool_results.append(result)

        # Step 3: Reasoning model synthesizes
        answer = self.reasoner.synthesize(
            user_query,
            tool_results
        )

        return answer


# ----------------------------
# RUN
# ----------------------------

agent = AgentSystem()

response = agent.run(
    "What's the weather in hamberg?"
)

print("\nFINAL ANSWER")
print(response)

# Reasoning LLM → “what should I do?”
# Tool LLM      → “how do I call the function?”
# Python        → “actually do it”

# In your architecture

# You now have 3 roles:

# 1. Reasoning model

# Decides what needs to be done

# 2. Tool model (qwen3:8b here)

# Turns plan → structured function calls

# 3. Python executor

# Actually runs tools

