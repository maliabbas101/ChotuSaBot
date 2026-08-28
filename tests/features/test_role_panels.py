import role_panels
import server_config as cfg


def test_exclusive_panel_splits_into_pages_of_25():
    roles = [cfg.ColorRole(f"Color{i}", "#000000") for i in range(30)]
    views = role_panels.build_exclusive_panel_views(roles, "test-color")

    assert len(views) == 2
    assert len(views[0].children) == 25
    assert len(views[1].children) == 5


def test_exclusive_panel_single_page_for_small_list():
    roles = [cfg.ColorRole(f"Color{i}", "#000000") for i in range(6)]
    views = role_panels.build_exclusive_panel_views(roles, "test-color-small")
    assert len(views) == 1
    assert len(views[0].children) == len(roles)


def test_real_color_roles_paginate_correctly():
    # server_config.COLOR_ROLES currently has more than 25 real Discord
    # roles, so it must span multiple pages/messages.
    views = role_panels.build_exclusive_panel_views(cfg.COLOR_ROLES, "color")
    total_buttons = sum(len(v.children) for v in views)
    assert total_buttons == len(cfg.COLOR_ROLES)
    assert all(len(v.children) <= 25 for v in views)


def test_toggle_panel_button_custom_ids_are_stable_and_unique():
    views = role_panels.build_toggle_panel_views(cfg.HOBBY_ROLES, "hobby")
    custom_ids = [b.custom_id for view in views for b in view.children]

    assert len(custom_ids) == len(set(custom_ids))
    for role in cfg.HOBBY_ROLES:
        assert f"toggle_role:hobby:{role.name}" in custom_ids


def test_exclusive_panel_button_custom_ids_use_group_key():
    views = role_panels.build_exclusive_panel_views(cfg.COLOR_ROLES, "color")
    custom_ids = [b.custom_id for view in views for b in view.children]
    for role in cfg.COLOR_ROLES:
        assert f"exclusive_role:color:{role.name}" in custom_ids


def test_all_persistent_views_registers_color_notif_hobby_and_region():
    views = role_panels.all_persistent_views()
    all_custom_ids = [b.custom_id for view in views for b in view.children]

    assert any(cid.startswith("exclusive_role:color:") for cid in all_custom_ids)
    assert any(cid.startswith("toggle_role:notif:") for cid in all_custom_ids)
    assert any(cid.startswith("toggle_role:hobby:") for cid in all_custom_ids)
    assert any(cid.startswith("exclusive_role:region:") for cid in all_custom_ids)


def test_all_persistent_views_skips_region_when_empty(monkeypatch):
    monkeypatch.setattr(cfg, "REGION_ROLES", [])

    views = role_panels.all_persistent_views()
    all_custom_ids = [b.custom_id for view in views for b in view.children]

    assert not any(cid.startswith("exclusive_role:region:") for cid in all_custom_ids)


def test_all_views_have_timeout_none_for_persistence():
    for view in role_panels.all_persistent_views():
        assert view.timeout is None


def test_nearest_color_emoji_matches_obvious_colors():
    assert role_panels.nearest_color_emoji("#FF0000") == "🔴"
    assert role_panels.nearest_color_emoji("#0000FF") == "🔵"
    assert role_panels.nearest_color_emoji("#00FF00") == "🟢"
    assert role_panels.nearest_color_emoji("#000000") == "⚫"
    assert role_panels.nearest_color_emoji("#FFFFFF") == "⚪"


def test_color_role_buttons_get_a_color_emoji():
    roles = [cfg.ColorRole("Fire", "#FF0000")]
    views = role_panels.build_exclusive_panel_views(roles, "test-color-emoji")
    button = views[0].children[0]
    assert str(button.emoji) == "🔴"


def test_region_role_buttons_keep_their_own_emoji():
    roles = [cfg.ToggleRole("Quettaite", "🍵")]
    views = role_panels.build_exclusive_panel_views(roles, "test-region-emoji")
    button = views[0].children[0]
    assert str(button.emoji) == "🍵"
