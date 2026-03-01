import os
import time
import requests

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID64 = os.getenv("STEAM_ID64")          # 朋友/自己個 SteamID64
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not STEAM_API_KEY or not STEAM_ID64 or not WEBHOOK_URL:
    raise SystemExit("Missing env vars: STEAM_API_KEY / STEAM_ID64 / DISCORD_WEBHOOK_URL")

last_status = None

def check_status():
    global last_status
    url = (
        "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        f"?key={STEAM_API_KEY}&steamids={STEAM_ID64}"
    )

    r = requests.get(url, timeout=10)
    data = r.json()
    player = data["response"]["players"][0]
    persona = player.get("personastate", None)

    if persona != last_status:
        last_status = persona
        if persona == 1:
            send_message("🟢 上線了")
        elif persona == 0:
            send_message("⚫ 離線了")
        else:
            send_message(f"🟡 狀態變更：{persona}")

def send_message(message):
    requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)

while True:
    check_status()
    time.sleep(60)