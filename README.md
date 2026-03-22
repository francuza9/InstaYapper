# InstaYapper

A Python bot that monitors an Instagram DM thread — including group chats — and responds when @mentioned. Uses Groq's free API with Llama 3.3 70B for generating replies. Built for private conversations — not a production service.

## Prerequisites

- Python 3.10+
- **ffmpeg** with libopus support (required for voice note replies)
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
- An Instagram account for the bot (use a separate account, not your main one)
- A free Groq API key from [console.groq.com](https://console.groq.com)

## Setup

1. **Clone and install dependencies:**

   ```bash
   git clone <repo-url>
   cd instagram_bot
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your values:

   - `INSTAGRAM_USERNAME` — the bot's Instagram username
   - `INSTAGRAM_PASSWORD` — the bot's Instagram password
   - `GROQ_API_KEY` — your API key from [console.groq.com](https://console.groq.com)
   - `GROUP_THREAD_ID` — the thread ID of the DM conversation (see below)
   - `BOT_DISPLAY_NAME` — the bot's Instagram handle without the `@`

3. **Find your group thread ID:**

   ```bash
   python find_thread.py
   ```

   This will list your recent DM threads with their IDs. Copy the thread ID of the conversation you want the bot in and paste it into `GROUP_THREAD_ID` in your `.env` file.

4. **Run the bot:**

   ```bash
   python bot.py
   ```

   The bot will start polling the DM thread every 30-45 seconds. Press `Ctrl+C` to stop.

## Customizing the Personality

Edit `system_prompt.txt` to change how the bot behaves. The `{BOT_DISPLAY_NAME}` placeholder gets replaced with the bot's name at runtime. No need to restart — the prompt is loaded on startup.

## Voice Messages Setup

Voice replies require web cookies from an authenticated Instagram browser session. These cookies let the bot upload audio without programmatic login.

1. **Open Instagram in your browser** and log into the bot account.

2. **Open Developer Tools** — press `F12`.

3. **Find the cookies:**
   - **Chrome:** go to the **Application** tab → **Cookies** → `https://www.instagram.com`
   - **Firefox:** go to the **Storage** tab → **Cookies** → `https://www.instagram.com`

4. **Copy these cookie values** into your `.env` file:

   | Cookie name | `.env` variable |
   |------------|-----------------|
   | `csrftoken` | `WEB_CSRFTOKEN` |
   | `datr` | `WEB_DATR` |
   | `ds_user_id` | `WEB_DS_USER_ID` |
   | `ig_did` | `WEB_IG_DID` |
   | `mid` | `WEB_MID` |
   | `rur` | `WEB_RUR` |
   | `sessionid` | `WEB_SESSIONID` |

5. **Note:** These cookies expire periodically. If voice messages stop working, repeat the steps above to refresh them.

> **Important:** Do NOT log out of the bot account in your browser after copying cookies. Logging out invalidates the session and voice messages will stop working. If you do log out, or if cookies expire naturally, you'll need to log back in and copy all the cookies again into `.env`. The bot will automatically detect expired cookies and fall back to text-only mode until you refresh them.

## Configuration

Edit `config.py` to tweak bot behavior without touching credentials or code:

| Setting | Default | Description |
|---------|---------|-------------|
| `REPLY_ONLY_WHEN_MENTIONED` | `False` | `True` = only reply when @mentioned, `False` = reply to every message |
| `VOICE_CHANCE` | `1.0` | Chance of replying with a voice message (0.0–1.0) |
| `TTS_LANGUAGE` | `"en"` | Language code for text-to-speech |
| `POLL_MIN` / `POLL_MAX` | `10` / `15` | Polling interval range in seconds |
| `REPLY_DELAY_MIN` / `REPLY_DELAY_MAX` | `1` / `3` | Delay before sending a reply (looks more human) |
| `REPLY_COOLDOWN` | `15` | Minimum seconds between replies |
| `CONTEXT_MESSAGES` | `20` | How many recent messages to send as context to the LLM |

## How It Works

- Polls the DM thread every 10-15 seconds (randomized)
- By default, replies to every new message. Set `REPLY_ONLY_WHEN_MENTIONED = True` in `config.py` to only reply when @mentioned.
- Sends recent messages as conversation context to Llama 3.3 70B via Groq
- Replies with a short delay to look more human
- Has a cooldown between replies to avoid spamming
- Saves the Instagram session to `session.json` to avoid re-logging in each time

## Troubleshooting

**"Instagram challenge required"**
Instagram detected unusual login activity. Open the Instagram app on your phone, approve the login, then restart the bot. This is common on first login or after a long break.

**"Rate limited by Instagram"**
The bot is making too many requests. It will automatically back off for 5 minutes. If this happens frequently, increase `POLL_MIN` and `POLL_MAX` in `bot.py`.

**Session issues**
Delete `session.json` and restart the bot to force a fresh login.

**Bot not responding**
- Make sure `BOT_DISPLAY_NAME` matches the bot's Instagram username exactly (without `@`)
- Check that `GROUP_THREAD_ID` is correct (run `find_thread.py` again)
- Check the console logs for errors

**Groq API errors**
- Verify your API key at [console.groq.com](https://console.groq.com)
- Free tier has rate limits — the bot handles this gracefully but may skip replies under heavy use

## Warning

This bot uses an unofficial Instagram API (`instagrapi`). Instagram may flag, restrict, or ban the bot account. Use a throwaway account, not your main one. This is against Instagram's Terms of Service — use at your own risk.
