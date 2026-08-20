import role_panels
import server_config as cfg


def test_exclusive_panel_splits_into_pages_of_25():
    roles = [cfg.ColorRole(f"Color{i}", "#000000") for i in range(30)]
    views = role_panels.build_exclusive_panel_views(roles, "test-color")

    assert len(views) == 2
    assert len(views[0].children) == 25
    assert len(views[1].children) == 5


def test_exclusive_panel_single_page_for_small_list():
    views = role_panels.build_exclusive_panel_views(cfg.COLOR_ROLES, "color")
    assert len(views) == 1
    assert len(views[0].children) == len(cfg.COLOR_ROLES)


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


def test_all_persistent_views_registers_color_notif_hobby_but_skips_empty_region():
    assert cfg.REGION_ROLES == []  # sanity check of current server_config state

    views = role_panels.all_persistent_views()
    all_custom_ids = [b.custom_id for view in views for b in view.children]

    assert any(cid.startswith("exclusive_role:color:") for cid in all_custom_ids)
    assert any(cid.startswith("toggle_role:notif:") for cid in all_custom_ids)
    assert any(cid.startswith("toggle_role:hobby:") for cid in all_custom_ids)
    assert not any(cid.startswith("exclusive_role:region:") for cid in all_custom_ids)


def test_all_views_have_timeout_none_for_persistence():
    for view in role_panels.all_persistent_views():
        assert view.timeout is None
