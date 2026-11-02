from types import SimpleNamespace

from thread_router.bot import thread_author


def person(name, uid, bot=False):
    return SimpleNamespace(display_name=name, id=uid, bot=bot)


def test_author_is_the_poster():
    msg = SimpleNamespace(author=person("Pilot", 1), mentions=[])
    assert thread_author(msg) == ("Pilot", 1)


def test_bot_message_uses_first_mentioned_person():
    # "@recruit is hunting for a recruiter!" from the Authlink bot
    msg = SimpleNamespace(
        author=person("Authlink", 9, bot=True), mentions=[person("Other bot", 8, True), person("Recruit", 5)]
    )
    assert thread_author(msg) == ("Recruit", 5)


def test_bot_message_without_mention_keeps_the_bot():
    msg = SimpleNamespace(author=person("Authlink", 9, bot=True), mentions=[])
    assert thread_author(msg) == ("Authlink", 9)
    assert thread_author(None) == ("Unknown", None)
