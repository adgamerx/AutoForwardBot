<div align="center">
  <img src="https://files.catbox.moe/uevfz8.jpg" alt="ADx Auto Forward Bot" width="720">
</div>

<h1 align="center">ADx Auto Forward Bot</h1>

<p align="center">
  A Telegram bot that keeps one channel mirrored into another.<br>
  Forward an entire channel in bulk, only the latest <code>N</code> posts, or let it
  auto forward every new post as it is published.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="Pyrogram" src="https://img.shields.io/badge/library-pyrofork-2CA5E0">
  <img alt="MongoDB" src="https://img.shields.io/badge/database-MongoDB-47A248?logo=mongodb&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-GPL--3.0-blue">
</p>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#deployment">Deployment</a> ·
  <a href="#troubleshooting">Troubleshooting</a>
</p>

---

## Features

### Channel mirroring

| Capability | What it does |
|---|---|
| **Auto forward** | Every new post in a source channel is forwarded to your target channel automatically. |
| **Bulk forward** | Forward a channel's history in one job with live progress, ETA and cancel. |
| **Latest N only** | Forward just the newest messages instead of the whole history. |
| **Skip offset** | Drop the first `N` messages, then forward the rest. |
| **Multiple rules** | Run several auto forward rules at once, each with its own source, target, account and mode. |
| **Resume after restart** | Interrupted bulk jobs and active auto forward rules continue where they stopped. |

### Delivery

| Mode | What it does |
|---|---|
| **Copy mode** | Sends messages without a forward tag; your custom caption, buttons and protected content apply. |
| **Forward tag mode** | Keeps the original "forwarded from" tag on every message. |
| **Public channels** | Works without admin rights in the source when using a bot that can read it. |
| **Private channels** | Works through a userbot that is a member of the source. |
| **Restricted content** | Optional protected/secure message delivery. |
| **Any media** | Text, photo, video, document, audio, voice, animation, sticker and polls. |

### Filtering and control

| Setting | What it does |
|---|---|
| **Type filters** | Toggle each message type on or off. |
| **Keyword allow-list** | Only forward files whose name contains one of your keywords. |
| **Extension block-list** | Skip files with specific extensions. |
| **Size limit** | Forward files larger than, smaller than, or exactly `N` MB. |
| **Duplicate skipping** | Optional per-user MongoDB tracking of already forwarded files. |
| **Custom caption** | Template with `{filename}`, `{size}` and `{caption}` placeholders. |
| **Custom buttons** | Add inline URL buttons to every forwarded message. |
| **Per-rule controls** | Pause, resume, switch mode or delete an auto forward rule at any time. |
| **Access control** | Owner-only admin commands, force subscription and broadcast. |

---

## How auto forward works

Each auto forward rule owns a background watcher:

1. It remembers the last source message id it handled (`last_id`).
2. Every `AUTOFORWARD_INTERVAL` seconds (default `30`) it reads the newest message
   id of the source channel.
3. Everything newer than `last_id` is fetched in batches and delivered to the
   target, and `last_id` is advanced after every batch — so a crash repeats at
   most one batch.
4. If the bot was offline for a long time, only `AUTOFORWARD_MAX_PER_CYCLE`
   messages are drained per check, so the target is never flooded.
5. Rules are stored in MongoDB, so they survive restarts and are started again
   automatically when the bot boots.

Polling is used instead of Telegram `channel_post` updates so behaviour is
identical for bots and userbots, for channels the account is not admin in, and
across restarts.

---

## Quick start

```text
1. Create a bot            →  @BotFather  →  copy the bot token
2. Get API credentials     →  https://my.telegram.org  →  API_ID and API_HASH
3. Create a MongoDB URI    →  https://cloud.mongodb.com  →  DATABASE_URI
4. Deploy the bot          →  see Deployment
5. Open the bot in Telegram →  /start  →  /settings  →  /autoforward
```

Inside `/settings` you need at least:

- **Bots** → *Add Bot* (forward the token message from BotFather) or
  *Add User Bot* / *Login User Bot* for private sources.
- **Channels** → *Add Channel* (forward any message from your target channel).

The account you add must be an **admin with post permission** in the target
channel. For a private source channel it must also be a member of that channel.

---

## Requirements

- Python **3.10+** (the Docker image uses 3.11)
- A **MongoDB** database (Atlas free tier works)
- Telegram **API_ID** and **API_HASH**
- A bot token from **@BotFather**

---

## Usage

### `/settings`

| Menu | What it configures |
|---|---|
| Bots | Add or remove bot accounts, userbot session strings and phone-login userbots. |
| Channels | Add or remove target chats (forward a message from the chat to add it). |
| Caption | Custom caption template for videos and documents. |
| MongoDB | Optional per-user database used to remember duplicates across restarts. |
| Filters | Message type toggles and forward tags. |
| Button | Inline URL buttons added to every forwarded message. |
| Extra settings | Poll, protected content, size limit, extensions and keywords. |

### `/forward` — one-off bulk forward

1. Choose the account (only asked when you have more than one).
2. Choose the target channel (only asked when you have more than one).
3. Send the source channel **link** (`t.me/name/123`, private links too) or
   **forward its last message**.
4. Enter the **skip count** — how many of the oldest messages should be ignored
   (`0` = forward everything).
5. Enter how many of the **latest messages** should be forwarded
   (`0` = everything after the skip).
6. Confirm and watch the live progress; cancel any time with the button.

Example: `skip = 10`, `latest = 50` → forwards the newest 50 messages of a
channel, but never below message id 11.

### `/autoforward` — live mirroring

1. Pick the account that should run the rule.
2. Pick one of your saved target channels.
3. Send the source channel link, its `@username`, or forward one of its posts.
4. Choose the delivery mode:
   - **Copy** — no forward tag; custom caption, buttons and protected content apply.
   - **Forward** — keeps the original forward tag.
5. Optionally forward the latest `N` existing messages once (`0` = only new posts).

The rule then runs in the background. From the same panel you can pause, resume,
switch its mode, or delete it. If a rule fails (removed account, lost access,
wrong permissions) the bot tells you in chat and shows the error on the rule.

> Delivery happens on the next check, so expect up to `AUTOFORWARD_INTERVAL`
> seconds of delay after a source post is published.

### `/unequify`

Deletes duplicate documents inside a channel, using Telegram's
`file_unique_id` so the same file is recognised across re-uploads.
Requires a **userbot** account and admin rights in that channel.

### Admin commands

| Command | Description |
|---|---|
| `/stats` | Users, accounts, channels and running forward jobs. |
| `/broadcast` | Reply to any message to send it to every bot user. |
| `/resetall` | Reset the settings of every user. |
| `/restart` | Restart the bot process. |

### Command reference

| Command | Access | Description |
|---|---|---|
| `/start` | Everyone | Show the main menu and status. |
| `/settings` | Everyone | Bot accounts, channels and forwarding settings. |
| `/forward`, `/fwd` | Everyone | Start a bulk forwarding job. |
| `/autoforward`, `/af` | Everyone | Manage auto forward rules. |
| `/unequify` | Everyone | Delete duplicate files in a channel (userbot). |
| `/reset` | Everyone | Reset your own settings to defaults. |
| `/cancel` | Everyone | Reply inside any prompt to abort it. |
| `/stats` | Owner | Bot statistics. |
| `/broadcast` | Owner | Broadcast a replied message to all users. |
| `/resetall` | Owner | Reset all users' settings. |
| `/restart` | Owner | Restart the bot. |

`Owner` = the numeric ids in `BOT_OWNER_ID`.

---

## Configuration

Everything is configured through environment variables read by `config.py`.
Start from the template:

```bash
cp .env.example .env
```

`.env` is gitignored. The bot loads it automatically at startup (python-dotenv)
and `docker compose` reads the same file through `env_file`, so one file works
for local runs and containers. Variables that already exist in the environment
always win over the file. Only the required block matters for a working
deployment; everything else has a sensible default.

### Required

| Variable | Description |
|---|---|
| `API_ID` | Telegram API id from https://my.telegram.org |
| `API_HASH` | Telegram API hash |
| `BOT_TOKEN` | Bot token from @BotFather |
| `BOT_OWNER_ID` | Your Telegram user id. Multiple ids separated by spaces |
| `DATABASE_URI` | MongoDB connection string (`mongodb+srv://...`) |

### Optional

| Variable | Default | Description |
|---|---|---|
| `DATABASE_NAME` | `Cluster0` | MongoDB database name. |
| `BOT_SESSION` | `bot` | Session name used for the main bot. |
| `PICS` | default banner | Image URL used on the start and settings screens. |
| `LOG_CHANNEL` | empty | Channel id for new-user/new-bot logs. Empty disables logging. |
| `FORCE_SUB_CHANNEL` | empty | Channel the user must join before using the bot. Empty disables force sub. |
| `FORCE_SUB_ON` | `True` | Enable force subscription (only used when a channel is set). |

### Branding

| Variable | Default | Description |
|---|---|---|
| `BOT_NAME` | `ADx Auto Forward Bot` | Name shown across the UI. |
| `BOT_USERNAME` | `ADxAutoForwardBot` | Bot username without `@`, used in links. |
| `DEVELOPER_NAME` | `ADx` | Developer name on the about page. |
| `UPDATES_CHANNEL` | `https://t.me/ADxUpdates` | Updates link used in buttons. |
| `SUPPORT_GROUP` | `https://t.me/ADxSupport` | Support link used in buttons. |
| `REPO_URL` | this repository | Source link on the about page. |
| `BOT_VERSION` | `V-3.0.0` | Version label on the about page. |

### Auto forward tuning

| Variable | Default | Description |
|---|---|---|
| `AUTOFORWARD_INTERVAL` | `30` | Seconds between checks (minimum `10`). |
| `AUTOFORWARD_BATCH` | `100` | Messages per Telegram request (maximum `200`). |
| `AUTOFORWARD_MAX_PER_CYCLE` | `300` | Backlog drained per check, so a long outage never floods the target. |

---

## Deployment

### VPS

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv

git clone https://github.com/adgamerx/ADx-AutoForward-Bot.git
cd ADx-AutoForward-Bot

python3 -m venv venv
source venv/bin/activate
pip3 install -U -r requirements.txt

cp .env.example .env    # fill in API_ID, API_HASH, BOT_TOKEN, BOT_OWNER_ID, DATABASE_URI
python3 main.py
```

Keep it alive with `systemd`, `screen`, `tmux` or a process manager of your
choice.

### Docker

```bash
docker build -t adx-auto-forward .
docker run -d --name adx-forward --env-file .env --restart unless-stopped adx-auto-forward
```

Or with the included compose file:

```bash
docker compose up -d --build
```

`start.sh` clones this repository inside the container; if you want the image to
run the local checkout instead, override the command:

```bash
docker run -d --env-file .env -v "$PWD":/fwdbot -w /fwdbot adx-auto-forward python3 main.py
```

### Koyeb

```text
Build command:  pip3 install -U -r requirements.txt
Run command:    python3 main.py
```

### Render

```text
Build command:  pip3 install -U -r requirements.txt
Start command:  gunicorn app:app & python3 main.py
```

`app.py` is a tiny Flask app used only as a keep-alive endpoint for platforms
that expect an HTTP port. It is not required elsewhere.

### Heroku / manifest deploys

`app.json`, `heroku.yml` and `Procfile` are included for platforms that consume
a manifest. They describe a single worker process only.

---

## Project structure

```text
ADx-AutoForward-Bot/
├── main.py            # entry point (python3 main.py)
├── bot.py             # Pyrogram client, startup and restore of running jobs
├── config.py          # environment variables and runtime state
├── database.py        # MongoDB layer: users, accounts, channels, jobs, rules
├── translation.py     # every user facing string
├── app.py             # Flask keep-alive endpoint
├── logging.conf       # console + file logging setup
├── .env.example       # every supported environment variable, documented
├── requirements.txt
├── Dockerfile / docker-compose.yml / Procfile / heroku.yml / app.json / start.sh
└── plugins/
    ├── commands.py     # /start, /restart, help, about, status
    ├── settings.py     # /settings menus
    ├── public.py       # /forward (bulk)
    ├── regix.py        # bulk forwarding worker and progress UI
    ├── autoforward.py  # auto forward watcher and /autoforward panel
    ├── filters.py      # message type / keyword / size helpers
    ├── utils.py        # job state and shared parsing helpers
    ├── test.py         # account onboarding, /reset, /resetall
    ├── unequify.py     # /unequify
    └── broadcast.py    # /broadcast
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `You didn't add any bot/userbot` | Add an account in `/settings` → Bots. |
| `please set a to channel in /settings` | Add a target chat in `/settings` → Channels. |
| Forwarding fails right after you confirm | Make the account an admin in the target channel, then use the retry button. |
| Source chat cannot be read | Use a userbot that is a member of the private channel, or give the bot admin rights there. |
| Auto forward rule shows 🔴 with an error | Open `/autoforward` → the rule → read the error, fix access, then Resume. |
| New posts take a while to appear | Delivery happens on each check; lower `AUTOFORWARD_INTERVAL` for faster mirroring. |
| Start screen shows a join prompt | The bot cannot verify membership of `FORCE_SUB_CHANNEL`; set a valid channel or leave it empty. |
| Settings are not saved / bot stops right after start | Check `DATABASE_URI`, that the database user has read-write access, and that your server IP is allowed in MongoDB Atlas. |
| `Telegram is taking too long` | Telegram throttling; the job retries automatically. |

---

## Limits and disclaimer

- Telegram rate limits apply. The bot backs off on `FloodWait` and retries.
- Files above Telegram's upload limit (2 GB, or 4 GB for premium accounts) cannot be sent and are counted as failed in the job stats.
- Userbot sessions carry a real risk of account restrictions. Use them on an
  account you can afford to lose; the authors take no responsibility.
- Only forward content you have the rights to redistribute.

---

## License

Released under the **GNU General Public License v3.0** — see [LICENSE](LICENSE).

<div align="center">

Built with ❤️ by **ADx**

<a href="https://t.me/ADxUpdates">Updates channel</a> ·
<a href="https://t.me/ADxSupport">Support group</a>

</div>
