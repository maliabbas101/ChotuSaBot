from types import SimpleNamespace
from unittest.mock import AsyncMock

import entertainment
from data_store import JsonDataStore


def _message(content, channel_id=1, author_id=42, author_bot=False, display_name="Ali"):
    channel = SimpleNamespace(id=channel_id, send=AsyncMock())
    author = SimpleNamespace(
        id=author_id, bot=author_bot, display_name=display_name, mention=f"<@{author_id}>"
    )
    return SimpleNamespace(content=content, channel=channel, author=author)


async def test_check_timed_question_answer_ignores_when_no_active_question(tmp_path):
    entertainment._active_questions.clear()
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    msg = _message("echo", channel_id=999)
    await entertainment.check_timed_question_answer(store, msg)

    msg.channel.send.assert_not_called()


async def test_check_timed_question_answer_correct_riddle_guess_awards_no_score(tmp_path):
    entertainment._active_questions.clear()
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel_id = 555
    entertainment._active_questions[channel_id] = entertainment.ActiveQuestion(
        accepted_answers={"echo", "an echo"}, display_answer="echo", kind="riddle"
    )

    msg = _message("Echo", channel_id=channel_id)
    await entertainment.check_timed_question_answer(store, msg)

    msg.channel.send.assert_called_once()
    assert channel_id not in entertainment._active_questions
    scores = await store.get("trivia_scores", {})
    assert scores == {}


async def test_check_timed_question_answer_correct_trivia_guess_updates_score(tmp_path):
    entertainment._active_questions.clear()
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel_id = 777
    entertainment._active_questions[channel_id] = entertainment.ActiveQuestion(
        accepted_answers={"islamabad"}, display_answer="islamabad", kind="trivia"
    )

    msg = _message("islamabad", channel_id=channel_id, author_id=42, display_name="Ali")
    await entertainment.check_timed_question_answer(store, msg)

    scores = await store.get("trivia_scores", {})
    assert scores["42"] == {"name": "Ali", "score": 1}


async def test_check_timed_question_answer_ignores_bot_authors(tmp_path):
    entertainment._active_questions.clear()
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel_id = 888
    entertainment._active_questions[channel_id] = entertainment.ActiveQuestion(
        accepted_answers={"echo"}, display_answer="echo", kind="riddle"
    )
    msg = _message("echo", channel_id=channel_id, author_bot=True)

    await entertainment.check_timed_question_answer(store, msg)

    msg.channel.send.assert_not_called()
    assert channel_id in entertainment._active_questions


async def test_check_timed_question_answer_wrong_guess_leaves_question_active(tmp_path):
    entertainment._active_questions.clear()
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel_id = 321
    entertainment._active_questions[channel_id] = entertainment.ActiveQuestion(
        accepted_answers={"echo"}, display_answer="echo", kind="riddle"
    )
    msg = _message("not it", channel_id=channel_id)

    await entertainment.check_timed_question_answer(store, msg)

    msg.channel.send.assert_not_called()
    assert channel_id in entertainment._active_questions
