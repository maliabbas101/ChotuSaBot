"""One-time script: posts the notification (ping) role self-assign panel.

Usage: python scripts/setup_notification_roles.py --channel roles
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from _role_setup_common import parse_channel_arg, post_panel  # noqa: E402
import role_panels  # noqa: E402
import server_config as cfg  # noqa: E402


async def main() -> None:
    channel_name = parse_channel_arg("Post the notification-role panel.")
    views = role_panels.build_toggle_panel_views(cfg.NOTIFICATION_ROLES, "notif")
    await post_panel(
        channel_name,
        title="Notification roles",
        body="Toggle pings for the stuff you care about. Click again to remove.",
        views=views,
    )


if __name__ == "__main__":
    asyncio.run(main())
