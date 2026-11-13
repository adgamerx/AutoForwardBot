<p align="center">
<img src="https://files.catbox.moe/uevfz8.jpg"/>

<hr>

# ADx Auto Forward Bot

A Telegram bot that keeps one channel mirrored into another. Forward existing
messages in bulk or let it auto forward every new post the moment it is published.

# FEATURES
 - **Auto Forward** - every new post is forwarded to your channel automatically.
 - Forward Only The Latest N Messages.
 - Forward Messages From Public & Private Channels.
 - Supports Broadcasts.
 - Custom Caption & Buttons.
 - Support Restricted Chats.
 - Skip Duplicate Messages.
 - Message Type Filters.
 - Filter By Extensions, Keywords & File Size.
 - Multiple Source & Target Channels.
 - Forward Videos, Photos, Documents & Other Media.
 - Forwarding Progress & Statistics.
 - MongoDB Database Support.
 - Docker Support.
<details>
 
<summary>More Features</summary>
 
<br>
 
 - Custom Forward Tags.
 - Skip Specific Messages.
 - Copy Mode Or Forward Tag Mode.
 - Per Rule Pause / Resume / Delete.
 - Automatic Resume After A Bot Restart.
 - Cancel Running Forward Tasks.
 - Protected Message Support.
 - Userbot/Pyrogram Session Support.
 - Configurable Forwarding Filters.
 - Duplicate File Detection.
 - Database-Based Message Tracking.

</details>

<hr>

# CONFIGS VARIABLES

Set these variables before starting the bot.

| Variable | Required | Description |
|---|---|---|
| `API_ID` | Yes | Telegram API ID from https://my.telegram.org |
| `API_HASH` | Yes | Telegram API hash |
| `BOT_TOKEN` | Yes | Bot token from BotFather |
| `BOT_OWNER_ID` | Yes | Admin/owner Telegram user ID(s), separated by spaces |
| `BOT_SESSION` | No | Bot session name. Default: `bot` |
| `PICS` | No | Start/help image URL |
| `DATABASE_URI` | Yes | MongoDB connection URI |
| `DATABASE_NAME` | No | MongoDB database name. Default: `Cluster0` |
| `LOG_CHANNEL` | No | Telegram log channel ID. Leave empty to disable logging |
| `FORCE_SUB_CHANNEL` | No | Force-subscription channel URL/username. Empty disables force sub |
| `FORCE_SUB_ON` | No | Enable/disable force subscription. Default: `True` |
| `BOT_NAME` | No | Display name used across the bot UI |
| `BOT_USERNAME` | No | Bot username without `@`, used in bot links |
| `DEVELOPER_NAME` | No | Name shown in the about page |
| `UPDATES_CHANNEL` | No | Updates channel link used in buttons |
| `SUPPORT_GROUP` | No | Support group link used in buttons |
| `REPO_URL` | No | Source repository link |
| `BOT_VERSION` | No | Version label shown in the about page |
| `AUTOFORWARD_INTERVAL` | No | Seconds between auto forward checks. Default: `30` (minimum `10`) |
| `AUTOFORWARD_BATCH` | No | Messages per Telegram request. Default: `100` (max `200`) |
| `AUTOFORWARD_MAX_PER_CYCLE` | No | Backlog drained per check, so a long downtime never floods the target. Default: `300` |

<hr>

# Files

```text
ADx-AutoForward-Bot/
├── Dockerfile
├── Procfile
├── app.json
├── app.py
├── bot.py
├── config.py
├── database.py
├── heroku.yml
├── logging.conf
├── main.py
├── requirements.txt
├── start.sh
├── translation.py
└── plugins/
    ├── broadcast.py
    ├── commands.py
    ├── public.py
    ├── regix.py
    ├── settings.py
    ├── test.py
    ├── unequify.py
    └── utils.py
```

<hr>

# DEPLOYEMENT SUPPORT
## Koyeb

```text
Build:
pip3 install -U -r requirements.txt

Run:
python3 main.py
```

## Render

```text
Build:
pip3 install -U -r requirements.txt

Start:
gunicorn app:app & python3 main.py
```

## VPS

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv

git clone https://github.com/ADx/ADx-AutoForward-Bot.git
cd ADx-AutoForward-Bot

python3 -m venv venv
source venv/bin/activate

pip3 install -U -r requirements.txt

python3 main.py
```
<hr>

# ALL COMMANDS

```
start - Start the bot.
forward - Forward messages (optionally only the latest N).
autoforward - Create and manage auto forward rules.
unequify - Delete dublicate files in channel.
settings - Configure your settings.
cancel - Cancel ongoing forwarding.
stats - To check bot stats (Admin Only)
resetall - To reset all user settings. (Admin Only)
broadcast - To broadcast any message to all users (Admin Only)
restart - Restart the bot (Admin Only)
```

# AUTO FORWARD

`/autoforward` mirrors a channel without any manual work:

1. Pick the bot or userbot that should run the rule.
2. Pick one of your target channels (added in `/settings`).
3. Send the source channel link, its `@username`, or forward one of its posts.
4. Choose the delivery mode:
   - **Copy** - no forward tag, your custom caption and buttons apply.
   - **Forward** - keeps the original forward tag.
5. Optionally forward the latest `N` existing messages once (enter `0` for only new posts).

From then on the bot checks the source channel every `AUTOFORWARD_INTERVAL`
seconds and forwards everything new. Rules survive restarts and can be paused,
resumed, switched between modes or deleted from the same panel.

Your `/settings` filters (message types, keywords, extensions, file size) and
protected-content option apply to auto forward as well.

> The selected bot/userbot must be an admin with post permission in the target
> channel. For private source channels it must be a member of the source too.

## Developer

**ADx**

<hr>

<p align="center">
  Built with ❤️ by <b>ADx</b>
</p>

<p align="center">
  📢 <a href="https://t.me/ADxUpdates">Updates Channel</a>
  &nbsp; • &nbsp;
  💬 <a href="https://t.me/ADxSupport">Support Group</a>
</p>

<p align="center">
  ⭐ If you find this project useful, don't forget to star the repository!
</p>
