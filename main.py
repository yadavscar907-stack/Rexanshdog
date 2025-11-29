import os
import time
import threading
import json
import random
import requests
from flask import Flask
from instagrapi import Client

# --- ENV CONFIG ---
SESSION_ID = os.getenv("SESSION_ID")
GROUP_IDS = os.getenv("GROUP_IDS", "")
GROUP_NAMES = os.getenv("GROUP_NAMES", "")
MESSAGE_TEXT = os.getenv("MESSAGE_TEXT", "Hello 👋")
SELF_URL = os.getenv("SELF_URL", "")
PORT = int(os.getenv("PORT", 10000))

# --- SETTINGS ---
BURST_COUNT = 3
DELAY_BETWEEN_MSGS = 40
REFRESH_DELAY = 30
NAME_CHANGE_INTERVAL = 240
SELF_PING_INTERVAL = 60
KEEPALIVE_CHECK_INTERVAL = 90

# --- RANDOM EMOJIS LIST ---
EMOJIS = ["🔥","😎","🐍","🤭","🐶","🐷","🗿","💀","🎀","😠","🌪","💫","🥶","😔"]

def rand_emoji():
    return random.choice(EMOJIS)

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot running — full anti-sleep mode active"

# --- MESSAGE SENDER ---
def send_message(cl, gid, msg):
    try:
        final_msg = f"{msg}{rand_emoji()}"
        cl.direct_send(final_msg, thread_ids=[int(gid)])
        print(f"✅ Sent message to {gid}   ➜ {final_msg}")
        return True
    except Exception as e:
        print(f"⚠ Error sending to {gid}: {e}")
        return False

# --- MESSAGE LOOP ---
def message_loop(cl, gid, gname):
    while True:
        print(f"\n🚀 Sending messages to {gname or gid}")
        for i in range(BURST_COUNT):
            ok = send_message(cl, gid, MESSAGE_TEXT)
            if not ok:
                print("⚠ Message failed, retrying after 5 minutes...")
                time.sleep(300)
            else:
                print(f"🕒 Waiting {DELAY_BETWEEN_MSGS}s before next message...")
                time.sleep(DELAY_BETWEEN_MSGS)
        print(f"✅ Burst complete for {gname or gid}, refreshing for {REFRESH_DELAY}s...\n")
        time.sleep(REFRESH_DELAY)

# --- GROUP NAME CHANGER ---
def name_changer(cl, gids, gnames):
    while True:
        for i, gid in enumerate(gids):
            base = gnames[i] if i < len(gnames) else None
            if not base:
                continue

            new_title = f"{base}{rand_emoji()}"

            try:
                variables = {"thread_fbid": gid, "new_title": new_title}
                payload = {"doc_id": "29088580780787855", "variables": json.dumps(variables)}
                resp = cl.private.post("https://www.instagram.com/api/graphql/", data=payload)

                if resp.status_code == 200:
                    print(f"✨ Name changed ➜ {new_title}")
                else:
                    print(f"⚠ Name change failed: {resp.text[:100]}")
            except Exception as e:
                print(f"⚠ Exception changing name for {gid}: {e}")

        print(f"🕓 Waiting {NAME_CHANGE_INTERVAL}s before next name change round...\n")
        time.sleep(NAME_CHANGE_INTERVAL)

# --- SELF PING ---
def self_ping():
    while True:
        if SELF_URL:
            try:
                requests.get(SELF_URL, timeout=10)
                print("🔁 Self ping successful")
            except Exception as e:
                print(f"⚠ Self ping error: {e}")
        time.sleep(SELF_PING_INTERVAL)

# --- RENDER ANTI-SLEEP PING ---
def render_ping():
    while True:
        try:
            if SELF_URL:
                requests.get(SELF_URL)
                print("🔁 Render Anti-Sleep Ping Sent")
        except:
            print("⚠ Render ping failed")
        time.sleep(50)

# --- FAKE LOAD GENERATOR ---
def fake_load():
    while True:
        x = 0
        for i in range(300000):
            x += i
        time.sleep(20)

# --- WATCHDOG ---
def keepalive_checker():
    while True:
        print("🧠 Keepalive check running...")
        try:
            requests.get("https://google.com", timeout=5)
            print("🌐 Internet OK")
        except:
            print("⚠ Internet unstable — rechecking soon...")
        time.sleep(KEEPALIVE_CHECK_INTERVAL)

def main():
    if not SESSION_ID or not GROUP_IDS:
        print("❌ SESSION_ID or GROUP_IDS missing in environment!")
        return

    gids = [g.strip() for g in GROUP_IDS.split(",") if g.strip()]
    gnames = [n.strip() for n in GROUP_NAMES.split(",")] if GROUP_NAMES else []

    cl = Client()
    try:
        cl.login_by_sessionid(SESSION_ID)
        print("✅ Logged in successfully")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return

    # Start message threads
    for i, gid in enumerate(gids):
        gname = gnames[i] if i < len(gnames) else ""
        threading.Thread(target=message_loop, args=(cl, gid, gname), daemon=True).start()

    # Start name changer
    threading.Thread(target=name_changer, args=(cl, gids, gnames), daemon=True).start()

    # Self ping
    threading.Thread(target=self_ping, daemon=True).start()

    # Render anti-sleep ping
    threading.Thread(target=render_ping, daemon=True).start()

    # Fake load
    threading.Thread(target=fake_load, daemon=True).start()

    # Watchdog
    threading.Thread(target=keepalive_checker, daemon=True).start()

    # Flask
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
