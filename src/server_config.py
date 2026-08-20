"""
Single source of truth for server-specific names (channels, roles, persona).

Edit this file to re-theme the bot for a different server. Nothing else in
the codebase should hardcode a channel or role name — always import from here.

Channel/role lookups are done by *name* at runtime (via discord.utils.get),
so you only need to keep the strings below in sync with the actual channel
and role names in your Discord server.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Server identity / persona
# ---------------------------------------------------------------------------

SERVER_NAME = "Quetta Tea Corner"
BOT_NAME = "ChotuSaBot"

BOT_PERSONA = (
    "You are ChotuSaBot, the chai-corner helper of Quetta Tea Corner, a "
    "casual Pakistani hangout server. Speak in a natural Roman Urdu/English "
    "mix (like real desi group-chat texting), keep it short and casual, "
    "cheeky and warm rather than formal or corporate. Use emojis naturally "
    "but don't overdo it. Never lecture, never sound like a customer-support "
    "bot. If the conversation turns serious — grief, loss, crisis, someone "
    "clearly upset or in danger — drop the jokes completely and either stay "
    "quiet or respond with simple, genuine warmth. Never joke into a serious "
    "moment."
)


# ---------------------------------------------------------------------------
# Channels (by name, without the leading '#')
# ---------------------------------------------------------------------------

LOG_CHANNEL = "khulla-chitta"
CONFESSIONS_CHANNEL = "raaz-ki-baat"
INTRO_CHANNEL = "intro"
IMAGE_ONLY_CHANNELS = ["artnclicks", "foodie", "memes"]

# Optional themed content command — Quetta Tea Corner already has a #rekhta
# channel, so the /rekhta (random Urdu poetry) command is a natural fit.
REKHTA_CHANNEL = "rekhta"
ENABLE_REKHTA_COMMAND = True

# Sticky message kept as the most-recent post in INTRO_CHANNEL — reposted
# after every new introduction so it stays at the bottom.
STICKY_INTRO_MESSAGE = (
    "**New here? Introduce yourself like this:** \N{TEAPOT}\n"
    "> **Naam:** your name / what to call you\n"
    "> **Age:** (optional)\n"
    "> **Where you're from:**\n"
    "> **Chai order:** how you take your chai\n"
    "> **Here for:** what brought you to the server\n"
    "> **Random fact about you:**"
)


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
# These are placeholder sets. Edit names/colors/emoji to match real roles in
# your server before running scripts/setup_*_roles.py.


@dataclass(frozen=True)
class ColorRole:
    name: str
    hex_color: str


@dataclass(frozen=True)
class ToggleRole:
    name: str
    emoji: str = ""


COLOR_ROLES: list[ColorRole] = [
    ColorRole("Crimson", "#DC143C"),
    ColorRole("Ocean", "#1E90FF"),
    ColorRole("Emerald", "#2ECC71"),
    ColorRole("Amber", "#FFC107"),
    ColorRole("Violet", "#8E44AD"),
    ColorRole("Rose", "#FF6FA5"),
]

NOTIFICATION_ROLES: list[ToggleRole] = [
    ToggleRole("VC Ping", "🔊"),
    ToggleRole("Chat Ping", "💬"),
    ToggleRole("Game Ping", "🎮"),
    ToggleRole("Event Ping", "📅"),
]

HOBBY_ROLES: list[ToggleRole] = [
    ToggleRole("Gaming", "🎮"),
    ToggleRole("Art", "🎨"),
    ToggleRole("Music", "🎵"),
    ToggleRole("Reading", "📚"),
    ToggleRole("Foodie", "🍽️"),
]

# Region/affinity roles are optional for this server — leave empty until
# real sub-community names are provided. If populated, the role-panel setup
# script will treat these as mutually exclusive (like color roles).
REGION_ROLES: list[ToggleRole] = []


# ---------------------------------------------------------------------------
# Known bump/listing bots whose invites don't behave like normal member
# invites — keyed by the bot account's username (lowercase, substring match)
# — used to produce a friendly fallback label instead of "Unknown" when the
# join can be attributed to that bot's inviter account.
# ---------------------------------------------------------------------------

KNOWN_EXTERNAL_INVITE_LABELS: dict[str, str] = {
    "disboard": "via Disboard bump",
}

FALLBACK_INVITE_LABEL = "via an expired or untracked invite link"
