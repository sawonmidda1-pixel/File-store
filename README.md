# Shappno-Codex File Store Bot — support files

Put `database.py` and `config.py` in the same GitHub repository folder as your main bot script.

## Required environment variables
- `BOT_TOKEN`: Telegram bot token from BotFather
- `ADMIN_IDS`: your Telegram numeric user ID (multiple IDs separated by commas)
- `FORCE_CHANNELS`: public channel usernames without @, comma-separated (optional)
- `OWNER_USERNAME`: owner username without @ (optional)
- `REFERRAL_COINS`: coins earned by referrer (default 10)
- `NEW_USER_REF_COINS`: coins for referred new user (default 5)

## Run
Build command: `pip install -r requirements.txt`
Start command: `python bot.py`

Rename your uploaded main Python file to `bot.py` before deploying.
The SQLite database file is created automatically as `bot_data.sqlite3`.
For persistent data on a hosting platform, attach persistent disk/storage and place the DB there.
