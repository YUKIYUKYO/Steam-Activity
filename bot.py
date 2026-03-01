import requests
import time

STEAM_ID = "76561198147526761"
WEBHOOK_URL = "貼你Discord webhook URL喺度"

last_status = None

def check_status():
    global last_status
    
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=YOUR_STEAM_API_KEY&steamids={STEAM_ID}"
    
    response = requests.get(url)
    data = response.json()
    
    player = data["response"]["players"][0]
    personastate = player["personastate"]

    if personastate != last_status:
        last_status = personastate
        
        if personastate == 1:
            send_message("🟢 上線了")
        elif personastate == 0:
            send_message("⚫ 離線了")

def send_message(message):
    payload = {
        "content": message
    }
    requests.post(WEBHOOK_URL, json=payload)

while True:
    check_status()
    time.sleep(60)
