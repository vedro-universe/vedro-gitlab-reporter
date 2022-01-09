from contextlib import contextmanager
from typing import Optional
from unittest.mock import Mock, call, patch
from uuid import uuid4

import pytest
from baby_steps import given, then, when
from rich.style import Style
from vedro.core import Dispatcher
from vedro.events import ArgParsedEvent, ScenarioFailedEvent, ScenarioRunEvent, StepFailedEvent
from vedro.plugins.director import Reporter
from vedro.plugins.director.rich.test_utils import (
    console_,
    dispatcher,
    make_parsed_args,
    make_scenario_result,
    make_step_result,
)

from vedro_gitlab_reporter import GitlabReporter

__all__ = ("dispatcher", "console_")


@pytest.fixture()
def reporter(console_) -> GitlabReporter:
    return GitlabReporter(lambda: console_)


@contextmanager
def patch_uuid(uuid: Optional[str] = None):
    if uuid is None:
        uuid = str(uuid4())
    with patch("uuid.uuid4", Mock(return_value=uuid)):
        yield uuid


def test_gitlab_reporter():
    with when:
        reporter = GitlabReporter()

    with then:
        assert isinstance(reporter, Reporter)


@pytest.mark.asyncio
async def test_reporter_scenario_run_event(*, dispatcher: Dispatcher,
                                           reporter: GitlabReporter, console_: Mock):
    with given:
        reporter.subscribe(dispatcher)

        scenario_result = make_scenario_result()
        event = ScenarioRunEvent(scenario_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert console_.mock_calls == [
            call.out(f"* {scenario_result.scenario.namespace}", style=Style.parse("bold"))
        ]


@pytest.mark.asyncio
async def test_reporter_scenario_failed_event_verbose0(*, dispatcher: Dispatcher,
                                                       reporter: GitlabReporter, console_: Mock):
    with given:
        reporter.subscribe(dispatcher)
        await dispatcher.fire(ArgParsedEvent(make_parsed_args(verbose=0)))

        scenario_result = make_scenario_result().mark_failed()
        event = ScenarioFailedEvent(scenario_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert console_.mock_calls == [
            call.out(f" ✗ {scenario_result.scenario.subject}", style=Style.parse("red"))
        ]


@pytest.mark.asyncio
async def test_reporter_scenario_failed_event_verbose1(*, dispatcher: Dispatcher,
                                                       reporter: GitlabReporter, console_: Mock):
    with given:
        reporter.subscribe(dispatcher)
        await dispatcher.fire(ArgParsedEvent(make_parsed_args(verbose=1)))

        step_result = make_step_result().mark_failed().set_started_at(1.0).set_ended_at(3.0)
        scenario_result = make_scenario_result(step_results=[step_result]).mark_failed()
        event = ScenarioFailedEvent(scenario_result)

    with when, patch_uuid() as uuid:
        await dispatcher.fire(event)

    with then:
        assert console_.mock_calls == [
            call.out(f" ✗ {scenario_result.scenario.subject}", style=Style.parse("red")),
            call.file.write(f"\x1b[0Ksection_start:{int(step_result.started_at)}:{uuid}"
                            "[collapsed=true]\r\x1b[0K"),
            call.out(f"    ✗ {step_result.step_name}", style=Style.parse("red")),
            call.file.write(f"\x1b[0Ksection_end:{int(step_result.ended_at)}:{uuid}\r\x1b[0K")
        ]


@pytest.mark.asyncio
async def test_reporter_scenario_failed_event_verbose2(*, dispatcher: Dispatcher,
                                                       reporter: GitlabReporter, console_: Mock):
    with given:
        reporter.subscribe(dispatcher)
        await dispatcher.fire(ArgParsedEvent(make_parsed_args(verbose=2)))

        scenario_result = make_scenario_result()
        await dispatcher.fire(ScenarioRunEvent(scenario_result))
        console_.reset_mock()

        scenario_result.set_scope({"key": "val"})
        step_result = make_step_result().mark_failed()
        await dispatcher.fire(StepFailedEvent(step_result))

        scenario_result = scenario_result.mark_failed()
        scenario_result.add_step_result(step_result)
        event = ScenarioFailedEvent(scenario_result)

    with when, patch_uuid() as uuid:
        await dispatcher.fire(event)

    with then:
        assert console_.mock_calls == [
            call.out(f" ✗ {scenario_result.scenario.subject}", style=Style.parse("red")),
            call.out(f"    ✗ {step_result.step_name}", style=Style.parse("red")),
            call.file.write(f"\x1b[0Ksection_start:0:{uuid}[collapsed=true]\r\x1b[0K"),
            call.out("      key: ", style=Style.parse("blue")),
            call.out("\"val\""),
            call.file.write(f"\x1b[0Ksection_end:0:{uuid}\r\x1b[0K")
        ]
