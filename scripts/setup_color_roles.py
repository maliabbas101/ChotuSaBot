"""One-time script: posts the color-role self-assign panel.

Usage: python scripts/setup_color_roles.py --channel roles
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from _role_setup_common import parse_channel_arg, post_panel  # noqa: E402
import role_panels  # noqa: E402
import server_config as cfg  # noqa: E402


async def main() -> None:
    channel_name = parse_channel_arg("Post the color-role panel.")
    views = role_panels.build_exclusive_panel_views(cfg.COLOR_ROLES, "color")
    await post_panel(
        channel_name,
        title="Pick a color",
        body=(
            "Click a button below to set your name color. Click it again to remove it.\n"
            "-# The circle on each button is the closest match — Discord buttons can't "
            "show the exact shade."
        ),
        views=views,
    )


if __name__ == "__main__":
    asyncio.run(main())
