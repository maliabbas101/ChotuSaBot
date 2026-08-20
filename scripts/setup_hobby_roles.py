"""One-time script: posts the hobby role self-assign panel.

Usage: python scripts/setup_hobby_roles.py --channel roles
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from _role_setup_common import parse_channel_arg, post_panel  # noqa: E402
import role_panels  # noqa: E402
import server_config as cfg  # noqa: E402


async def main() -> None:
    channel_name = parse_channel_arg("Post the hobby-role panel.")
    views = role_panels.build_toggle_panel_views(cfg.HOBBY_ROLES, "hobby")
    await post_panel(
        channel_name,
        title="Hobby roles",
        body="Pick as many as you like — helps people find others into the same stuff.",
        views=views,
    )


if __name__ == "__main__":
    asyncio.run(main())
