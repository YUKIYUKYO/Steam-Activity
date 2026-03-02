import os
import time
import requests

print("Bot starting...", flush=True)

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID64 = os.getenv("STEAM_ID64")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not STEAM_API_KEY or not STEAM_ID64 or not DISCORD_WEBHOOK_URL:
    raise SystemExit("Missing env vars")

STATE_MAP = {
    0: "⚫ 離線/隱身",
    1: "🟢 在線",
    2: "🔴 忙碌",
    3: "🟡 離開",
    4: "💤 打盹",
    5: "🔵 想交易",
    6: "🟣 想玩",
}

last_status = None
last_game = None


def send_message(message):
    try:
        requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message},
            timeout=10
        )
    except Exception as e:
        print("Webhook error:", e, flush=True)


def check_status():
    global last_status, last_game

    try:
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            "key": STEAM_API_KEY,
            "steamids": STEAM_ID64
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        players = data.get("response", {}).get("players", [])

        if not players:
            print("No player data", flush=True)
            return

        p = players[0]

        personastate = p.get("personastate")
        game = p.get("gameextrainfo")

        if last_status is None:
            last_status = personastate
            last_game = game
            print("Initialized", flush=True)
            return

        # 狀態變更
        if personastate != last_status:
            last_status = personastate
            state_text = STATE_MAP.get(personastate, personastate)

            if personastate == 1 and game:
                send_message(f"{state_text}｜正在玩：{game}")
            else:
                send_message(f"狀態變更：{state_text}")

        # 遊戲變更（只在線時）
        if personastate == 1 and game != last_game:

            if last_game is None and game:
                send_message(f"🎮 開始玩：{game}")

            elif last_game and game and game != last_game:
                send_message(f"🎮 轉玩：{last_game} → {game}")

            elif last_game and game is None:
                send_message(f"🛑 停止玩：{last_game}")

        last_game = game

    except Exception as e:
        print("Steam API error:", e, flush=True)


counter = 0

while True:
    check_status()

    counter += 1
    if counter % 6 == 0:
        print("heartbeat...", flush=True)

    time.sleep(10)