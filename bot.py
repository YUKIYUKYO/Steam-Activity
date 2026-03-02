import os
import time
import requests
print("Bot starting...", flush=True)

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID64 = os.getenv("STEAM_ID64")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not STEAM_API_KEY or not STEAM_ID64 or not WEBHOOK_URL:
    raise SystemExit("Missing environment variables")

last_status = None

def send_message(message):
    try:
        requests.post(
            WEBHOOK_URL,
            json={"content": message},
            timeout=5
        )
    except Exception as e:
        print("Webhook error:", e)

def check_status():
    global last_status
    
    try:
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            "key": STEAM_API_KEY,
            "steamids": STEAM_ID64
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        players = data.get("response", {}).get("players", [])
        if not players:
            print("No player data returned")
            return

        personastate = players[0].get("personastate")

        if last_status is None:
            last_status = personastate
            return

        if personastate != last_status:
            last_status = personastate

            if personastate == 1:
                send_message("🟢 上線了")
            elif personastate == 0:
                send_message("⚫ 離線了")

except Exception as e:
    print("Steam API error:", e)


counter = 0

while True:
    check_status()
    counter += 1

    if counter % 6 == 0:
        print("heartbeat...", flush=True)

    time.sleep(10)