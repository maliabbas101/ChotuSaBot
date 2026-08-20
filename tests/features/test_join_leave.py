from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord

import join_leave
import server_config as cfg


def _invite(code, uses, inviter=None):
    return SimpleNamespace(code=code, uses=uses, inviter=inviter)


def _guild(invites, vanity_url_code=None, vanity_invite=None):
    return SimpleNamespace(
        invites=AsyncMock(return_value=invites),
        vanity_url_code=vanity_url_code,
        vanity_invite=AsyncMock(return_value=vanity_invite),
    )


async def test_resolve_used_invite_finds_the_incremented_code():
    human_inviter = SimpleNamespace(bot=False, name="Umair", __str__=lambda self: "Umair#0001")
    guild = _guild(invites=[_invite("abc123", uses=6, inviter=human_inviter)])
    cached = {"abc123": 5}

    invite, label = await join_leave.resolve_used_invite(guild, cached)

    assert invite is not None
    assert invite.code == "abc123"
    assert "Umair" in label


async def test_resolve_used_invite_labels_known_bump_bot():
    bot_inviter = SimpleNamespace(bot=True, name="Disboard", __str__=lambda self: "Disboard#0001")
    guild = _guild(invites=[_invite("bump1", uses=11, inviter=bot_inviter)])
    cached = {"bump1": 10}

    invite, label = await join_leave.resolve_used_invite(guild, cached)

    assert label == cfg.KNOWN_EXTERNAL_INVITE_LABELS["disboard"]


async def test_resolve_used_invite_falls_back_to_vanity():
    guild = _guild(
        invites=[_invite("static1", uses=5, inviter=None)],
        vanity_url_code="quettatea",
        vanity_invite=_invite("quettatea", uses=21),
    )
    cached = {"static1": 5, "quettatea": 20}

    invite, label = await join_leave.resolve_used_invite(guild, cached)

    assert invite is None
    assert label == "via server vanity URL"


async def test_resolve_used_invite_falls_back_to_generic_label_when_untraceable():
    guild = _guild(invites=[_invite("static1", uses=5, inviter=None)], vanity_url_code=None)
    cached = {"static1": 5}

    invite, label = await join_leave.resolve_used_invite(guild, cached)

    assert invite is None
    assert label == cfg.FALLBACK_INVITE_LABEL


async def test_resolve_used_invite_handles_forbidden_without_crashing():
    guild = SimpleNamespace(
        invites=AsyncMock(side_effect=discord.Forbidden.__new__(discord.Forbidden))
    )
    invite, label = await join_leave.resolve_used_invite(guild, {})
    assert invite is None
    assert label == cfg.FALLBACK_INVITE_LABEL
