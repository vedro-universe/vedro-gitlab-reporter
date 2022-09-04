from unittest.mock import Mock, call

import pytest
from baby_steps import given, then, when
from vedro.core import Dispatcher, ScenarioStatus, StepStatus
from vedro.events import ScenarioReportedEvent, StepFailedEvent

from vedro_gitlab_reporter import GitlabCollapsableMode

from ._utils import (
    director,
    dispatcher,
    fire_arg_parsed_event,
    fire_scenario_run_event,
    gitlab_reporter,
    make_aggregated_result,
    make_step_result,
    patch_uuid,
    printer_,
)

__all__ = ("dispatcher", "director", "gitlab_reporter", "printer_")  # fixtures


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_collapsable_steps(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher, collapsable_mode=GitlabCollapsableMode.STEPS)
        scenario_result = await fire_scenario_run_event(dispatcher)
        scenario_result.set_scope({"key": "val"})

        step_result = make_step_result().mark_failed().set_started_at(1.0).set_ended_at(3.0)
        await dispatcher.fire(StepFailedEvent(step_result))
        scenario_result.add_step_result(step_result)

        aggregated_result = make_aggregated_result(scenario_result.mark_failed())
        event = ScenarioReportedEvent(aggregated_result)

        printer_.reset_mock()
        printer_.pretty_format = lambda self: "'val'"

    with when, patch_uuid() as uuid:
        await dispatcher.fire(event)

    with then:
        section_start, section_end = int(step_result.started_at), int(step_result.ended_at)
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.FAILED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),

            call.console.file.write(
                f"\x1b[0Ksection_start:{section_start}:{uuid}[collapsed=true]\r\x1b[0K"),
            call.print_step_name(step_result.step_name,
                                 StepStatus.FAILED,
                                 elapsed=step_result.elapsed,
                                 prefix=" " * 3),
            call.print_scope_key("key", indent=5, line_break=True),
            call.print_scope_val("'val'"),
            call.console.file.write(f"\x1b[0Ksection_end:{section_end}:{uuid}\r\x1b[0K"),
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_collapsable_vars(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher, collapsable_mode=GitlabCollapsableMode.VARS)
        scenario_result = await fire_scenario_run_event(dispatcher)
        scenario_result.set_scope({"key": "val"})

        step_result = make_step_result().mark_failed().set_started_at(1.0).set_ended_at(3.0)
        await dispatcher.fire(StepFailedEvent(step_result))
        scenario_result.add_step_result(step_result)

        aggregated_result = make_aggregated_result(scenario_result.mark_failed())
        event = ScenarioReportedEvent(aggregated_result)

        printer_.reset_mock()
        printer_.pretty_format = lambda self: "'val'"

    with when, patch_uuid() as uuid:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.FAILED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),

            call.print_step_name(step_result.step_name,
                                 StepStatus.FAILED,
                                 elapsed=step_result.elapsed,
                                 prefix=" " * 3),

            call.console.file.write(f"\x1b[0Ksection_start:0:{uuid}[collapsed=true]\r\x1b[0K"),
            call.print_scope_key("key", indent=5, line_break=True),
            call.print_scope_val("'val'"),
            call.console.file.write(f"\x1b[0Ksection_end:0:{uuid}\r\x1b[0K"),
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_collapsable_scope(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher, collapsable_mode=GitlabCollapsableMode.SCOPE)
        scenario_result = await fire_scenario_run_event(dispatcher)
        scenario_result.set_scope({"key": "val"})

        step_result = make_step_result().mark_failed().set_started_at(1.0).set_ended_at(3.0)
        await dispatcher.fire(StepFailedEvent(step_result))
        scenario_result.add_step_result(step_result)

        aggregated_result = make_aggregated_result(scenario_result.mark_failed())
        event = ScenarioReportedEvent(aggregated_result)

        printer_.reset_mock()

    with when, patch_uuid() as uuid:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.FAILED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),
            call.print_step_name(step_result.step_name,
                                 StepStatus.FAILED,
                                 elapsed=step_result.elapsed,
                                 prefix=" " * 3),

            call.console.file.write(f"\x1b[0Ksection_start:0:{uuid}[collapsed=true]\r\x1b[0K"),
            call.print_scope(scenario_result.scope),
            call.console.file.write(f"\x1b[0Ksection_end:0:{uuid}\r\x1b[0K"),
        ]
