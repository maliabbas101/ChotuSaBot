"""One-time script: posts the region/affinity role self-assign panel.

Usage: python scripts/setup_region_roles.py --channel take-roles
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from _role_setup_common import parse_channel_arg, post_panel  # noqa: E402
import role_panels  # noqa: E402
import server_config as cfg  # noqa: E402


async def main() -> None:
    if not cfg.REGION_ROLES:
        print(
            "server_config.REGION_ROLES is empty — add role names/emoji there "
            "before running this script."
        )
        return

    channel_name = parse_channel_arg("Post the region-role panel.")
    views = role_panels.build_exclusive_panel_views(cfg.REGION_ROLES, "region")
    await post_panel(
        channel_name,
        title="Pick your region",
        body="Click a button below to set your region role. Click it again to remove it.",
        views=views,
    )


if __name__ == "__main__":
    asyncio.run(main())
