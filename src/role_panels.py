"""Button-panel views for self-assignable roles.

Two flavors:
  * Exclusive panels (color roles, region roles) — clicking a role removes
    any other role from the same group first, so a member holds at most one.
  * Toggle panels (notification roles, hobby roles) — clicking a role just
    adds/removes that single role; multiple may be held at once.

Panels are posted once via scripts/setup_*_roles.py and then registered as
persistent views (custom_id based, timeout=None) in main_bot.py's
setup_hook so they keep working across bot restarts without needing to be
resent.

Discord caps a View at 25 components (5 rows x 5), so role lists longer
than 25 are split across multiple messages/pages, each its own View.
"""

from __future__ import annotations

import logging

import discord

import server_config as cfg

logger = logging.getLogger(__name__)

MAX_BUTTONS_PER_VIEW = 25


def _chunk(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


class ExclusiveRoleButton(discord.ui.Button):
    def __init__(self, group_key: str, role_name: str):
        super().__init__(
            label=role_name,
            style=discord.ButtonStyle.secondary,
            custom_id=f"exclusive_role:{group_key}:{role_name}",
        )
        self.group_key = group_key
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "This only works inside the server.", ephemeral=True
            )
            return

        target_role = discord.utils.get(guild.roles, name=self.role_name)
        if target_role is None:
            await interaction.response.send_message(
                f"The **{self.role_name}** role doesn't exist on this server yet — "
                "ask a mod to create it.",
                ephemeral=True,
            )
            return

        group_role_names = {r.name for r in _group_roles(self.group_key)}
        member_group_roles = [r for r in member.roles if r.name in group_role_names]

        if target_role in member_group_roles:
            await member.remove_roles(target_role, reason="Self-assign: removed via role panel")
            await interaction.response.send_message(
                f"Removed **{self.role_name}**.", ephemeral=True
            )
            return

        if member_group_roles:
            await member.remove_roles(*member_group_roles, reason="Self-assign: swapping role")
        await member.add_roles(target_role, reason="Self-assign via role panel")
        await interaction.response.send_message(f"You're now **{self.role_name}**.", ephemeral=True)


class ToggleRoleButton(discord.ui.Button):
    def __init__(self, group_key: str, role_name: str, emoji: str = ""):
        super().__init__(
            label=role_name,
            emoji=emoji or None,
            style=discord.ButtonStyle.secondary,
            custom_id=f"toggle_role:{group_key}:{role_name}",
        )
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "This only works inside the server.", ephemeral=True
            )
            return

        target_role = discord.utils.get(guild.roles, name=self.role_name)
        if target_role is None:
            await interaction.response.send_message(
                f"The **{self.role_name}** role doesn't exist on this server yet — "
                "ask a mod to create it.",
                ephemeral=True,
            )
            return

        if target_role in member.roles:
            await member.remove_roles(target_role, reason="Self-unassign via role panel")
            await interaction.response.send_message(
                f"Removed **{self.role_name}**.", ephemeral=True
            )
        else:
            await member.add_roles(target_role, reason="Self-assign via role panel")
            await interaction.response.send_message(f"Added **{self.role_name}**.", ephemeral=True)


def _group_roles(group_key: str) -> list:
    return {
        "color": cfg.COLOR_ROLES,
        "region": cfg.REGION_ROLES,
    }[group_key]


class RolePanelView(discord.ui.View):
    """A single page of role buttons. timeout=None makes it persistent."""

    def __init__(self, buttons: list[discord.ui.Button]):
        super().__init__(timeout=None)
        for button in buttons:
            self.add_item(button)


def build_exclusive_panel_views(roles: list[cfg.ColorRole], group_key: str) -> list[RolePanelView]:
    pages = _chunk(roles, MAX_BUTTONS_PER_VIEW)
    return [
        RolePanelView([ExclusiveRoleButton(group_key, role.name) for role in page])
        for page in pages
    ]


def build_toggle_panel_views(roles: list[cfg.ToggleRole], group_key: str) -> list[RolePanelView]:
    pages = _chunk(roles, MAX_BUTTONS_PER_VIEW)
    return [
        RolePanelView([ToggleRoleButton(group_key, role.name, role.emoji) for role in page])
        for page in pages
    ]


def all_persistent_views() -> list[RolePanelView]:
    """Every view instance that must be re-registered on bot startup.

    Called from setup_hook via bot.add_view(view) for each returned view so
    button clicks keep working after a restart, without resending messages.
    """
    views: list[RolePanelView] = []
    views += build_exclusive_panel_views(cfg.COLOR_ROLES, "color")
    views += build_toggle_panel_views(cfg.NOTIFICATION_ROLES, "notif")
    views += build_toggle_panel_views(cfg.HOBBY_ROLES, "hobby")
    if cfg.REGION_ROLES:
        views += build_exclusive_panel_views(cfg.REGION_ROLES, "region")
    return views
