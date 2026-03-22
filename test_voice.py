#!/usr/bin/env python3
"""Standalone test for web voice upload — no instagrapi, no bot loop."""

import json
import os
import re
import subprocess

import requests
from dotenv import load_dotenv
from gtts import gTTS

load_dotenv()

THREAD_ID = os.getenv("CHAT_THREAD_ID")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def step(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")


# --- Step 0: Generate test M4A ---
step("Generating test audio")
tts = gTTS("This is a voice upload test", lang="en")
tts.save("/tmp/test_voice.mp3")
result = subprocess.run(
    ["ffmpeg", "-i", "/tmp/test_voice.mp3", "-c:a", "aac", "-b:a", "64k", "/tmp/test_voice.m4a", "-y"],
    capture_output=True,
)
if result.returncode != 0:
    print(f"ffmpeg failed: {result.stderr.decode()}")
    exit(1)
print("Created /tmp/test_voice.m4a")

# --- Step 1: Load browser cookies from .env ---
step("Loading browser cookies from .env")
session = requests.Session()
session.headers.update({"User-Agent": UA})

cookies = {
    "csrftoken": os.getenv("WEB_CSRFTOKEN"),
    "datr": os.getenv("WEB_DATR"),
    "ds_user_id": os.getenv("WEB_DS_USER_ID"),
    "ig_did": os.getenv("WEB_IG_DID"),
    "mid": os.getenv("WEB_MID"),
    "rur": os.getenv("WEB_RUR"),
    "sessionid": os.getenv("WEB_SESSIONID"),
}

missing = [k for k, v in cookies.items() if not v]
if missing:
    print(f"  Missing cookies: {', '.join(missing)}")
    print("  Fill in the WEB_* variables in your .env file.")
    exit(1)

cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
session.headers["Cookie"] = cookie_str

print(f"  Cookie header: {cookie_str[:120]}...")

# --- Step 2: Fetch web tokens ---
step("Fetching web tokens from /direct/")
resp = session.get("https://www.instagram.com/direct/", headers={
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
})
print(f"  Status: {resp.status_code}")
print(f"  HTML length: {len(resp.text)}")

print(f"\n  Cookie header being sent: {session.headers.get('Cookie', '')[:120]}...")

html = resp.text
fb_dtsg_match = re.search(r'"DTSGInitData".*?"token"\s*:\s*"([^"]+)"', html, re.DOTALL)
lsd_match = re.search(r'"LSD".*?"token"\s*:\s*"([^"]+)"', html, re.DOTALL)
jazoest_match = re.search(r'jazoest=(\d+)', html)

tokens = {}
for name, match in [("fb_dtsg", fb_dtsg_match), ("lsd", lsd_match), ("jazoest", jazoest_match)]:
    if match:
        tokens[name] = match.group(1)
        print(f"  {name}: {tokens[name][:30]}...")
    else:
        print(f"  {name}: NOT FOUND!")

if len(tokens) != 3:
    print("Token extraction failed!")
    exit(1)

# --- Step 3: Upload audio ---
step("Uploading audio to upload.php")

with open("/tmp/test_voice.m4a", "rb") as f:
    audio_data = f.read()
print(f"  Audio size: {len(audio_data)} bytes")

params = {
    "__d": "www",
    "__user": "0",
    "__a": "1",
    "__ccg": "GOOD",
    "__comet_req": "7",
    "__crn": "comet.igweb.PolarisDirectInboxRoute",
    "dpr": "1",
    "fb_dtsg": tokens["fb_dtsg"],
    "lsd": tokens["lsd"],
    "jazoest": tokens["jazoest"],
}

headers = {
    "X-FB-LSD": tokens["lsd"],
    "X-CSRFToken": cookies["csrftoken"],
    "X-ASBD-ID": "359341",
    "X-IG-App-ID": "936619743392459",
    "Origin": "https://www.instagram.com",
    "Referer": "https://www.instagram.com/direct/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

print(f"\n  Request params: {json.dumps(params, indent=4)}")
print(f"\n  Request headers: {json.dumps(headers, indent=4)}")
print(f"\n  Raw cookies: {cookies}")

upload_headers = {
    "User-Agent": UA,
    "Cookie": cookie_str,
    **headers,
}
resp = requests.post(
    "https://www.instagram.com/ajax/mercury/upload.php",
    params=params,
    headers=upload_headers,
    files={"farr": ("reply.m4a", audio_data, "audio/mp4")},
)

print(f"\n  Response status: {resp.status_code}")
print(f"  Response headers: {dict(resp.headers)}")
print(f"  Response body: {resp.text[:2000]}")

# Parse response
body = resp.text
if body.startswith("for (;;);"):
    body = body[len("for (;;);"):]

try:
    data = json.loads(body)
    print(f"\n  Parsed JSON: {json.dumps(data, indent=2)[:2000]}")
except json.JSONDecodeError as e:
    print(f"\n  JSON parse error: {e}")
    exit(1)

try:
    audio_id = data["payload"]["metadata"]["0"]["audio_id"]
    print(f"\n  audio_id: {audio_id}")
except (KeyError, TypeError) as e:
    print(f"\n  Failed to extract audio_id: {e}")
    print(f"  Full data: {json.dumps(data, indent=2)}")
    exit(1)

# --- Step 4: Send via GraphQL ---
step(f"Sending voice to thread {THREAD_ID}")

import random
variables = json.dumps({
    "attachment_fbid": str(audio_id),
    "thread_id": str(THREAD_ID),
    "offline_threading_id": str(random.randint(10**17, 10**18 - 1)),
    "reply_to_message_id": None,
})

graphql_headers = {
    "X-FB-Friendly-Name": "IGDirectMediaSendMutation",
    "X-CSRFToken": cookies["csrftoken"],
    "X-IG-App-ID": "936619743392459",
    "X-FB-LSD": tokens["lsd"],
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

graphql_data = {
    "fb_api_req_friendly_name": "IGDirectMediaSendMutation",
    "doc_id": "25604816565789936",
    "variables": variables,
    "fb_dtsg": tokens["fb_dtsg"],
    "lsd": tokens["lsd"],
    "jazoest": tokens["jazoest"],
    "__a": "1",
    "__d": "www",
    "__comet_req": "7",
    "server_timestamps": "true",
}

print(f"\n  GraphQL headers: {json.dumps(graphql_headers, indent=4)}")
print(f"\n  GraphQL data: {json.dumps(graphql_data, indent=4)}")

resp = session.post(
    "https://www.instagram.com/api/graphql",
    headers=graphql_headers,
    data=graphql_data,
)

print(f"\n  Response status: {resp.status_code}")
print(f"  Response body: {resp.text[:2000]}")

step("DONE!")
