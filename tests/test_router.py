from thread_router.models import ActionSpec, Result
from thread_router.router import reply_text, route


class Fake:
    def __init__(self, name, result=None, error=None):
        self.name, self.result, self.error, self.calls = name, result, error, []

    async def handle(self, thread, options):
        self.calls.append(options)
        if self.error:
            raise self.error
        return self.result


async def test_runs_every_action_of_the_channel(thread):
    a = Fake("a", Result(True, "A done", "https://a"))
    b = Fake("b", error=RuntimeError("boom"))
    rules = {100: [ActionSpec("a", {"x": 1}), ActionSpec("b")]}
    results = await route(thread, rules, {"a": a, "b": b})
    assert a.calls == [{"x": 1}]
    assert [r.ok for r in results] == [True, False]
    assert reply_text(results).splitlines()[0] == "✅ A done https://a"


async def test_channel_without_rule_does_nothing(thread):
    a = Fake("a", Result(True, "x"))
    assert await route(thread, {999: [ActionSpec("a")]}, {"a": a}) == []
    assert a.calls == []


async def test_bot_thread_runs_only_actions_that_allow_it(thread):
    from dataclasses import replace

    a, b = Fake("a", Result(True, "A")), Fake("b", Result(True, "B"))
    rules = {100: [ActionSpec("a"), ActionSpec("b", {"allow_bot_threads": True})]}
    results = await route(replace(thread, from_bot=True), rules, {"a": a, "b": b})
    assert a.calls == [] and len(b.calls) == 1
    assert [r.message for r in results] == ["B"]
