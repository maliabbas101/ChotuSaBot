"""JSON persistence round-trip: data written by one store instance must be
readable, intact, by a completely fresh store instance pointed at the same
file — simulating a bot restart.
"""

from pathlib import Path

from data_store import JsonDataStore


async def test_roundtrip_survives_a_fresh_store_instance(tmp_path: Path):
    path = tmp_path / "bot_data.json"

    writer = JsonDataStore(path)
    await writer.load()

    await writer.update_section(
        "trivia_scores", lambda s: s.update({"111": {"name": "Ali", "score": 5}})
    )
    await writer.update_section(
        "pet_system",
        lambda s: s.update(
            {
                "111": {
                    "name": "Chotu Jr.",
                    "hunger": 40,
                    "happiness": 70,
                    "last_interaction": "2026-08-20T00:00:00+00:00",
                }
            }
        ),
    )
    await writer.update_section("vc_time", lambda s: s.update({"111": 3600.0}))

    reader = JsonDataStore(path)
    data = await reader.load()

    assert data["trivia_scores"]["111"] == {"name": "Ali", "score": 5}
    assert data["pet_system"]["111"]["name"] == "Chotu Jr."
    assert data["vc_time"]["111"] == 3600.0


async def test_roundtrip_after_multiple_sequential_writes(tmp_path: Path):
    path = tmp_path / "bot_data.json"
    store = JsonDataStore(path)
    await store.load()

    for i in range(5):
        await store.update_section("vc_time", lambda s, i=i: s.update({str(i): i * 10}))

    reread = JsonDataStore(path)
    data = await reread.load()

    for i in range(5):
        assert data["vc_time"][str(i)] == i * 10
