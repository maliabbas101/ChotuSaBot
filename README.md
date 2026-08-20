# ChotuSaBot 🍵

A feature-rich Discord bot built for the **Quetta Tea Corner** community server. Handles moderation, channel automation, entertainment, role self-assignment, and Gemini-powered AI chat replies — no music, no database, low-RAM footprint.

Hosting target: any low-RAM PaaS (Pterodactyl/FeatherPanel, Railway, etc.) — runs comfortably under 100MB RAM since there's no voice/music dependency.

## Features

### 🤖 AI Chat Replies
- Probabilistically joins ongoing conversations using Gemini (flash-tier model) — feels like a lurking member, not a command-only bot
- Context-aware — reads the last ~12 messages in the channel before replying
- Per-user persona profiles — tracks each user's recent messages to bias tone/style
- Dead-chat revival — occasionally drops a casual message when a channel's been quiet for hours
- Serious-topic detection — suppresses AI replies entirely during grief/crisis conversations
- Uses the server's custom emojis naturally
- 1–4 key Gemini rotation — automatically switches keys on HTTP 429
- Output safety guard — blocks threats, self-harm phrases, and blocklisted slurs before anything is sent; regenerates once, then suppresses
- Strips the bot's own `@mention` out of conversation history before it's used as context

### 🛡️ Moderation
- `/purge [amount] [filter] [before_message_link]` — bulk-delete up to 100 messages, filterable by all/text/images/voice-attachments/links, with an optional message-link anchor
- Auto-deletes non-image messages in image-only channels (`#artnclicks`, `#foodie`, `#memes`), with a short auto-disappearing notice explaining the rule

### 📋 Channel Automation
- Auto-thread on every new post in `#raaz-ki-baat` (confessions)
- Auto-thread (welcome thread) on every new post in `#intro`
- Auto-thread on every image post in the image-only channels
- Sticky intro-format message kept as the most recent post in `#intro`

### 👋 Join/Leave Logs (`#khulla-chitta`)
- Join embed: username, invited-by, account age, member count
- Leave embed: username, join date, roles held, member count
- Invite-use tracking with graceful fallback (vanity URL / bump-bot / untraceable invite) instead of ever crashing or showing "Unknown"

### 🎮 Entertainment
- `/trivia` — trivia question, 2-minute timer, tracked leaderboard
- `/triviascores` — leaderboard
- `/riddle` — riddle, 5-minute timer
- `/wyr` — Would You Rather
- `/qotd` — Question of the Day
- `/roast @user` — friendly roast
- `/compliment @user` — compliment
- `/pomodoro [minutes]` — study timer, DMs (or pings) when it ends
- `/rekhta` — random Urdu poetry couplet (fits the server's `#rekhta` channel)

All content is static and defined in `src/question_bank.py` — no external API required.

### 🎨 Role Management
- Color roles — paginated button panel, one color at a time (mutually exclusive)
- Notification roles — VC Ping, Chat Ping, Game Ping, Event Ping (toggleable, multiple allowed)
- Hobby roles — Gaming, Art, Music, Reading, Foodie (toggleable, multiple allowed)
- Region/affinity roles — same exclusive-panel pattern, ready to populate once real sub-community names are decided (currently empty in `server_config.py`)

Panels are posted once via `scripts/setup_*_roles.py` and stay working across restarts (persistent views, re-registered in `setup_hook`).

### 📊 Utilities
- `/stats` — member count, online count, channel/role counts, server age
- `/vctime [user]` — cumulative voice-channel time
- `/adopt new|feed|play|status` — small virtual-pet gimmick
- `/tldr [count]` — Gemini-powered summary of the last 50–500 messages in a channel

## Server customization

Everything server-specific — persona, channel names, role lists — lives in **`src/server_config.py`**. Re-theme the bot for a different server by editing that one file; nothing else hardcodes a channel or role name.

Channels currently wired up:

| Purpose | Channel |
|---|---|
| Join/leave logs | `#khulla-chitta` |
| Confessions | `#raaz-ki-baat` |
| Intro / sticky message | `#intro` |
| Image-only | `#artnclicks`, `#foodie`, `#memes` |
| Urdu poetry | `#rekhta` |

## Setup

### Requirements
- Python 3.11+

### Installation

```bash
git clone <your-repo-url>
cd ChotuSaBot
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Environment variables

Copy `.env.example` to `.env` and fill in:

```env
DISCORD_TOKEN=your_bot_token

# Optional — leave all blank to run with AI features disabled.
# Get free keys at aistudio.google.com; keys from different Google
# accounts give you higher combined rate limits via rotation.
GEMINI_API_KEY_1=
GEMINI_API_KEY_2=
GEMINI_API_KEY_3=
GEMINI_API_KEY_4=
GEMINI_MODEL=gemini-2.0-flash

# Optional — only needed if you swap the static question bank for a live API.
API_NINJAS_KEY=
```

Moderation, roles, channel automation, and entertainment commands all work with **no Gemini key configured** — only AI chat replies and `/tldr` require one.

### Running

```bash
python src/main_bot.py
```

### One-time role panel setup

After the bot is in your server and the roles you want exist, post each panel once:

```bash
python scripts/setup_color_roles.py --channel roles
python scripts/setup_notification_roles.py --channel roles
python scripts/setup_hobby_roles.py --channel roles
python scripts/setup_region_roles.py --channel roles   # only if REGION_ROLES is populated
```

Panels are persistent — they keep working across bot restarts without needing to be reposted.

## Deployment

### Pterodactyl / FeatherPanel

Startup command:

```bash
pip install -r requirements.txt && python src/main_bot.py
```

Set `DISCORD_TOKEN`, `GEMINI_API_KEY_1`–`4` (optional), and `API_NINJAS_KEY` (optional) as environment variables in the panel.

### Railway / Nixpacks

`Procfile` and `nixpacks.toml` are included — push the repo and set the same environment variables in the Railway dashboard.

## Development

```bash
pip install -r requirements.txt
pytest -q
black --line-length 100 src tests scripts
flake8 src tests scripts
```

Tests are organized as:
- `tests/unit` — data store atomic writes/corruption recovery, retry backoff, question bank shape
- `tests/integration` — JSON persistence round-trips across store instances
- `tests/features` — moderation filters, role panels, invite resolution, timed trivia/riddle answers, AI helper functions
- `tests/e2e` — bot module import + full slash-command registration smoke test, no live token required

## Bot permissions required

- Read/Send Messages
- **Read Message History** (`/purge`, `/tldr` — both fetch past messages via `channel.history()`; without this Discord returns 403 Missing Access)
- Manage Messages (`/purge`, image-channel auto-delete)
- Manage Threads (auto-threading)
- Manage Roles (role panels — the bot's role must sit above every self-assignable role)
- Embed Links
- View Audit Log + Manage Server (invite tracking)
