import json
from pathlib import Path

import pytest

from data_store import DEFAULT_DATA, JsonDataStore


async def test_creates_file_with_defaults_when_missing(tmp_path: Path):
    path = tmp_path / "bot_data.json"
    store = JsonDataStore(path)

    data = await store.load()

    assert path.exists()
    assert data == DEFAULT_DATA
    assert json.loads(path.read_text(encoding="utf-8")) == DEFAULT_DATA


async def test_atomic_write_leaves_no_leftover_temp_files(tmp_path: Path):
    path = tmp_path / "bot_data.json"
    store = JsonDataStore(path)
    await store.load()

    store.data["vc_time"]["12345"] = 60
    await store.save()

    leftover_tmp_files = list(tmp_path.glob(f".{path.name}.*.tmp"))
    assert leftover_tmp_files == []
    assert json.loads(path.read_text(encoding="utf-8"))["vc_time"]["12345"] == 60


async def test_corrupt_file_recovers_with_defaults(tmp_path: Path):
    path = tmp_path / "bot_data.json"
    path.write_text("{not valid json!!", encoding="utf-8")
    store = JsonDataStore(path)

    data = await store.load()

    assert data == DEFAULT_DATA


async def test_non_object_json_root_recovers_with_defaults(tmp_path: Path):
    path = tmp_path / "bot_data.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    store = JsonDataStore(path)

    data = await store.load()

    assert data == DEFAULT_DATA


async def test_missing_top_level_keys_are_merged_in(tmp_path: Path):
    path = tmp_path / "bot_data.json"
    path.write_text(json.dumps({"pet_system": {"1": {"name": "Fluffy"}}}), encoding="utf-8")
    store = JsonDataStore(path)

    data = await store.load()

    assert data["pet_system"] == {"1": {"name": "Fluffy"}}
    assert "vc_time" in data
    assert "trivia_scores" in data


async def test_save_before_load_raises(tmp_path: Path):
    store = JsonDataStore(tmp_path / "bot_data.json")
    with pytest.raises(RuntimeError):
        await store.save()


async def test_update_section_mutates_and_persists(tmp_path: Path):
    path = tmp_path / "bot_data.json"
    store = JsonDataStore(path)
    await store.load()

    def mutate(section: dict) -> None:
        section["42"] = {"score": 3}

    await store.update_section("trivia_scores", mutate)

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["trivia_scores"]["42"] == {"score": 3}
