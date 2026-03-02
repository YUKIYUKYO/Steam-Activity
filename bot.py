import os
import time
import requests

print("Bot starting...", flush=True)

STEAM_API_KEY = os.getenv("STEAM_API_KEY", "").strip()
STEAM_ID64S = os.getenv("STEAM_ID64S", "").strip()  # can be "id1" or "id1,id2,id3"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))  # seconds

if not STEAM_API_KEY or not STEAM_ID64S or not DISCORD_WEBHOOK_URL:
    raise SystemExit("Missing env vars: STEAM_API_KEY / STEAM_ID64S / DISCORD_WEBHOOK_URL")

steam_ids = [x.strip() for x in STEAM_ID64S.split(",") if x.strip()]
if not steam_ids:
    raise SystemExit("STEAM_ID64S is empty or invalid")

PERSONA_TEXT = {
    0: "⚫ 離線/隱身",
    1: "🟢 在線",
    2: "🔴 忙碌",
    3: "🟡 離開",
    4: "💤 打盹",
    5: "🔵 想交易",
    6: "🟣 想玩",
}

# store last seen status per user
last_state = {}  # steamid -> dict(personastate=int, game=str|None, name=str)

session = requests.Session()

def send_message(text: str):
    try:
        r = session.post(
            DISCORD_WEBHOOK_URL,
            json={"content": text},
            timeout=8,
        )
        # Discord webhook returns 204 No Content on success
        if r.status_code not in (200, 204):
            print(f"Webhook error: {r.status_code} {r.text}", flush=True)
    except Exception as e:
        print("Webhook exception:", e, flush=True)

def fetch_players():
    # Steam API: GetPlayerSummaries (up to 100 steamids per call)
    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
    params = {"key": STEAM_API_KEY, "steamids": ",".join(steam_ids)}
    r = session.get(url, params=params, timeout=8)
    r.raise_for_status()
    data = r.json()
    players = data.get("response", {}).get("players", [])
    return players

def format_line(name: str, persona: int, game: str | None):
    persona_text = PERSONA_TEXT.get(persona, f"狀態({persona})")
    if game:
        return f"**{name}**：{persona_text}｜🎮 {game}"
    return f"**{name}**：{persona_text}"

def check_status_once():
    try:
        players = fetch_players()
        if not players:
            print("No player data returned", flush=True)
            return

        for p in players:
            sid = p.get("steamid")
            name = p.get("personaname", sid)
            persona = int(p.get("personastate", 0))
            game = p.get("gameextrainfo")  # only appears when playing a game

            prev = last_state.get(sid)

            # first time: just store, don't spam
            if prev is None:
                last_state[sid] = {"personastate": persona, "game": game, "name": name}
                continue

            prev_persona = prev["personastate"]
            prev_game = prev["game"]
            prev_name = prev["name"]

            # name change (optional)
            if name != prev_name:
                send_message(f"✏️ Steam 改名：**{prev_name}** → **{name}**")

            # status change (offline->online etc.)
            if persona != prev_persona:
                send_message(
                    f"🔔 狀態更新：{format_line(name, prev_persona, prev_game)} → {format_line(name, persona, game)}"
                )

            # game change (start playing / switch game / stop playing)
            if game != prev_game:
                if prev_game is None and game is not None:
                    send_message(f"🎮 開始玩：**{name}**｜{game}")
                elif prev_game is not None and game is None:
                    send_message(f"🛑 停止玩：**{name}**｜之前：{prev_game}")
                else:
                    send_message(f"🔄 換咗 game：**{name}**｜{prev_game} → {game}")

            last_state[sid] = {"personastate": persona, "game": game, "name": name}

    except Exception as e:
        print("Steam API error:", e, flush=True)

def main():
    print("Initialized", flush=True)

    counter = 0
    while True:
        check_status_once()
        counter += 1

        # 每 60 秒印一次心跳，方便你確認有 run 緊（但仍然每 10 秒 check）
        if counter % max(1, (60 // CHECK_INTERVAL)) == 0:
            print("heartbeat...", flush=True)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()