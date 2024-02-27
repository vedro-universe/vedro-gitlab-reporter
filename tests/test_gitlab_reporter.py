from unittest.mock import Mock, call

import pytest
from baby_steps import given, then, when
from vedro.core import AggregatedResult, Dispatcher
from vedro.core import MonotonicScenarioScheduler as ScenarioScheduler
from vedro.core import Report, ScenarioStatus
from vedro.events import (
    CleanupEvent,
    ScenarioFailedEvent,
    ScenarioPassedEvent,
    ScenarioReportedEvent,
    ScenarioRunEvent,
    StartupEvent,
)
from vedro.plugins.director import DirectorInitEvent, DirectorPlugin

from vedro_gitlab_reporter import GitlabReporter, GitlabReporterPlugin

from ._utils import (
    director,
    dispatcher,
    fire_arg_parsed_event,
    gitlab_reporter,
    make_aggregated_result,
    make_scenario_result,
    printer_,
)

__all__ = ("dispatcher", "director", "gitlab_reporter", "printer_")  # fixtures


async def test_subscribe(*, dispatcher: Dispatcher):
    with given:
        director_ = Mock(DirectorPlugin)

        reporter = GitlabReporterPlugin(GitlabReporter)
        reporter.subscribe(dispatcher)

    with when:
        await dispatcher.fire(DirectorInitEvent(director_))

    with then:
        assert director_.mock_calls == [
            call.register("gitlab", reporter)
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_startup(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        scheduler = ScenarioScheduler([])
        event = StartupEvent(scheduler)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_header()
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_run(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        scenario_result = make_scenario_result()
        event = ScenarioRunEvent(scenario_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.print_namespace.assert_called() is None
        assert len(printer_.mock_calls) == 1


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_run_same_namespace(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        scenario_result1 = make_scenario_result()
        await dispatcher.fire(ScenarioRunEvent(scenario_result1))
        printer_.reset_mock()

        scenario_result2 = make_scenario_result()
        event = ScenarioRunEvent(scenario_result2)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.print_namespace.assert_not_called() is None
        assert len(printer_.mock_calls) == 0


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_passed(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        scenario_result = make_scenario_result().mark_passed()
        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" ")
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_passed_with_extra_details(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        extra_details = '<details>'
        scenario_result = make_scenario_result(extra_details=extra_details).mark_passed()
        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),
            call.print_scenario_extra_details([extra_details],
                                              prefix="   ")
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_passed_with_default_show_path(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        scenario_result = make_scenario_result().mark_passed()
        await dispatcher.fire(ScenarioPassedEvent(scenario_result))

        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),
            call.print_scenario_extra_details([f"{aggregated_result.scenario.path.name}"],
                                              prefix=" " * 3)
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_passed_with_none_show_path(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher, show_paths=None)

        scenario_result = make_scenario_result().mark_passed()
        await dispatcher.fire(ScenarioPassedEvent(scenario_result))

        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        # no printed path of scenario info
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_passed_with_specified_show_path_included(
    *, dispatcher: Dispatcher, printer_: Mock
):
    with given:
        await fire_arg_parsed_event(dispatcher, show_paths=[ScenarioStatus.PASSED.value])

        scenario_result = make_scenario_result().mark_passed()
        await dispatcher.fire(ScenarioPassedEvent(scenario_result))

        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),
            call.print_scenario_extra_details([f"{aggregated_result.scenario.path.name}"],
                                              prefix=" " * 3)
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_passed_with_specified_show_path_not_included(
    *, dispatcher: Dispatcher, printer_: Mock
):
    with given:
        await fire_arg_parsed_event(dispatcher, show_paths=[ScenarioStatus.FAILED.value])

        scenario_result = make_scenario_result().mark_passed()
        await dispatcher.fire(ScenarioPassedEvent(scenario_result))

        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_failed_with_extra_details(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        extra_details = '<details>'
        scenario_result = make_scenario_result(extra_details=extra_details).mark_failed()
        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.FAILED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),
            call.print_scenario_extra_details([extra_details],
                                              prefix="   ")
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_failed(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        scenario_result = make_scenario_result().mark_failed()
        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.FAILED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" ")
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_failed_with_default_show_paths(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        scenario_result = make_scenario_result().mark_failed()
        await dispatcher.fire(ScenarioFailedEvent(scenario_result))

        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.FAILED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),
            call.print_scenario_extra_details([f"{aggregated_result.scenario.path.name}"],
                                              prefix=" " * 3)
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_failed_with_none_show_paths(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher, show_paths=None)

        scenario_result = make_scenario_result().mark_failed()
        await dispatcher.fire(ScenarioFailedEvent(scenario_result))

        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        # no printed path of scenario info
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.FAILED,
                                        elapsed=aggregated_result.elapsed,
                                        prefix=" "),
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_passed_aggregated_result(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        scenario_results = [
            make_scenario_result().mark_passed(),
            make_scenario_result().mark_passed(),
        ]

        aggregated_result = AggregatedResult.from_existing(scenario_results[0], scenario_results)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=None,
                                        prefix=" "),

            call.print_scenario_subject(aggregated_result.scenario_results[0].scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=scenario_results[0].elapsed,
                                        prefix=" │\n ├─[1/2] "),
            call.print_scenario_subject(aggregated_result.scenario_results[1].scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=scenario_results[1].elapsed,
                                        prefix=" │\n ├─[2/2] "),

            call.print_empty_line(),
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_passed_aggregated_result_with_extra_details(*, dispatcher: Dispatcher,
                                                                    printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        extra_details_1 = '<details1>'
        extra_details_2 = '<details2>'
        scenario_results = [
            make_scenario_result(extra_details=extra_details_1).mark_passed(),
            make_scenario_result(extra_details=extra_details_2).mark_passed(),
        ]

        aggregated_result = AggregatedResult.from_existing(scenario_results[0], scenario_results)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_scenario_subject(aggregated_result.scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=None,
                                        prefix=" "),

            call.print_scenario_subject(aggregated_result.scenario_results[0].scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=scenario_results[0].elapsed,
                                        prefix=" │\n ├─[1/2] "),
            call.print_scenario_extra_details([extra_details_1],
                                              prefix="           "),
            call.print_scenario_subject(aggregated_result.scenario_results[1].scenario.subject,
                                        ScenarioStatus.PASSED,
                                        elapsed=scenario_results[1].elapsed,
                                        prefix=" │\n ├─[2/2] "),
            call.print_scenario_extra_details([extra_details_2],
                                              prefix="           "),

            call.print_empty_line(),
        ]


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_scenario_unknown_status(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        scenario_result = make_scenario_result()
        aggregated_result = make_aggregated_result(scenario_result)
        event = ScenarioReportedEvent(aggregated_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == []


@pytest.mark.usefixtures(gitlab_reporter.__name__)
async def test_cleanup(*, dispatcher: Dispatcher, printer_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)

        report = Report()
        event = CleanupEvent(report)

    with when:
        await dispatcher.fire(event)

    with then:
        assert printer_.mock_calls == [
            call.print_empty_line(),
            call.print_report_summary(report.summary),
            call.print_report_stats(total=report.total,
                                    passed=report.passed,
                                    failed=report.failed,
                                    skipped=report.skipped,
                                    elapsed=report.elapsed)
        ]
