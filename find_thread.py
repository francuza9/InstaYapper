#!/usr/bin/env python3
"""Helper script to find your Instagram DM thread IDs."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from instagrapi import Client

SESSION_FILE = Path(__file__).parent / "session.json"


def login(username, password):
    cl = Client()
    if SESSION_FILE.exists():
        cl.load_settings(SESSION_FILE)
    try:
        cl.login(username, password)
    except Exception as e:
        print(f"Login failed: {e}")
        if SESSION_FILE.exists():
            print("Deleting old session and retrying...")
            SESSION_FILE.unlink()
            cl = Client()
            cl.login(username, password)
        else:
            sys.exit(1)
    cl.dump_settings(SESSION_FILE)
    return cl


def main():
    load_dotenv()

    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        print("Error: Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in your .env file")
        sys.exit(1)

    print(f"Logging in as {username}...")
    cl = login(username, password)
    print("Login successful!\n")

    print("Fetching recent DM threads...\n")
    threads = cl.direct_threads(amount=20)

    for thread in threads:
        participants = ", ".join(u.username for u in thread.users)
        title = thread.thread_title or "Untitled"
        thread_type = "Group" if len(thread.users) > 1 else "Direct"

        print(f"{'=' * 50}")
        print(f"Thread ID:    {thread.id}")
        print(f"Type:         {thread_type}")
        print(f"Title:        {title}")
        print(f"Participants: {participants}")
        if thread.messages:
            last_msg = thread.messages[0]
            preview = (last_msg.text or "[non-text message]")[:80]
            print(f"Last message: {preview}")
        print()

    print(f"{'=' * 50}")
    print("Copy the Thread ID of your group chat and paste it into GROUP_THREAD_ID in your .env file.")


if __name__ == "__main__":
    main()
