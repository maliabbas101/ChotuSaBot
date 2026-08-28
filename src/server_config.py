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
    ColorRole("Red", "#E74C3C"),
    ColorRole("Blue", "#3498DB"),
    ColorRole("Crimson", "#DC143C"),
    ColorRole("Emerald", "#50C878"),
    ColorRole("Sky", "#87CEEB"),
    ColorRole("Pearl", "#F0EAD6"),
    ColorRole("Pink", "#FF69B4"),
    ColorRole("Lavender", "#E6BEFF"),
    ColorRole("Rose", "#FF007F"),
    ColorRole("Gold", "#FFD700"),
    ColorRole("Silver", "#C0C0C0"),
    ColorRole("Violet", "#8A2BE2"),
    ColorRole("Lime", "#32CD32"),
    ColorRole("Maroon", "#3C0008"),
    ColorRole("Plum", "#9370DB"),
    ColorRole("Teal", "#008080"),
    ColorRole("Tangerine", "#FF8C00"),
    ColorRole("Gray", "#808080"),
    ColorRole("Cream", "#F5F5DC"),
    ColorRole("Fuchsia", "#FF1493"),
    ColorRole("Blush", "#FFB6C1"),
    ColorRole("Indigo", "#4B0082"),
    ColorRole("Lilac", "#DDA0DD"),
    ColorRole("Powder", "#ADD8E6"),
    ColorRole("Vanilla", "#FFEFD5"),
    ColorRole("Linen", "#FAF0E6"),
    ColorRole("Fire", "#FF0000"),
    ColorRole("Neon", "#00FF00"),
    ColorRole("Plasma", "#FF00FF"),
    ColorRole("Laser", "#00FFFF"),
    ColorRole("Azure", "#1E90FF"),
    ColorRole("Copper", "#A0522D"),
    ColorRole("Sand", "#D2B48C"),
    ColorRole("Bronze", "#CD853F"),
    ColorRole("Taupe", "#988C7E"),
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

# Region/affinity roles — mutually exclusive, matching roles already
# created in Quetta Tea Corner.
REGION_ROLES: list[ToggleRole] = [
    ToggleRole("Karachite", "🌊"),
    ToggleRole("Lahori", "🕌"),
    ToggleRole("Faisalabadi", "🏭"),
    ToggleRole("Peshawari", "🍢"),
    ToggleRole("Multani", "🍯"),
    ToggleRole("Islamabadi/Pindi", "🏛️"),
    ToggleRole("Quettaite", "🍵"),
    ToggleRole("Gujranwala", "🍗"),
    ToggleRole("Hyderabadi", "🍚"),
    ToggleRole("Gujrati", "🏺"),
    ToggleRole("Jhelum", "🌉"),
    ToggleRole("International", "🌍"),
]


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
