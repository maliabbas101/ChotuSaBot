from pathlib import Path

import safety_filter


def test_is_serious_topic_detects_grief():
    assert safety_filter.is_serious_topic("my grandma passed away last night, funeral is friday")


def test_is_serious_topic_detects_crisis_language():
    assert safety_filter.is_serious_topic("i honestly don't want to live anymore")


def test_is_serious_topic_false_for_normal_chat():
    assert not safety_filter.is_serious_topic("bro this game is so fun let's queue again")


def test_is_unsafe_output_detects_threat():
    assert safety_filter.is_unsafe_output("i will kill you if you do that again")


def test_is_unsafe_output_detects_self_harm_phrase():
    assert safety_filter.is_unsafe_output("lol just kys already")


def test_is_unsafe_output_false_for_normal_text():
    assert not safety_filter.is_unsafe_output("haha that meme killed me, so funny")


def test_blocklist_terms_are_detected(tmp_path: Path, monkeypatch):
    blocklist_file = tmp_path / "blocklist.txt"
    blocklist_file.write_text("# comment\nbadword\n", encoding="utf-8")

    monkeypatch.setattr(safety_filter, "BLOCKLIST_PATH", blocklist_file)
    safety_filter._load_blocklist.cache_clear()

    try:
        assert safety_filter.is_unsafe_output("that's such a badword to use")
        assert not safety_filter.is_unsafe_output("totally normal sentence")
    finally:
        safety_filter._load_blocklist.cache_clear()


def test_empty_blocklist_file_blocks_nothing_extra(tmp_path: Path, monkeypatch):
    blocklist_file = tmp_path / "blocklist.txt"
    blocklist_file.write_text("# nothing here yet\n", encoding="utf-8")

    monkeypatch.setattr(safety_filter, "BLOCKLIST_PATH", blocklist_file)
    safety_filter._load_blocklist.cache_clear()

    try:
        assert not safety_filter.is_unsafe_output("perfectly normal message")
    finally:
        safety_filter._load_blocklist.cache_clear()
