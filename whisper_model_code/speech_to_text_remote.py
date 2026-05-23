import requests

url = "http://hal9000.skim.th-owl.de:8003/transcribe"

with open("record_game.m4a", "rb") as f:
    response = requests.post(url, files={"file": f})

print(response.json())