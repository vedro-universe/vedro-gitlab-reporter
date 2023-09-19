import sys
from argparse import ArgumentParser, Namespace
from contextlib import contextmanager
from pathlib import Path
from time import monotonic_ns
from types import TracebackType
from typing import Optional, Union, cast
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from vedro import Config, Scenario
from vedro.core import (
    AggregatedResult,
    Dispatcher,
    ExcInfo,
    ScenarioResult,
    StepResult,
    VirtualScenario,
    VirtualStep,
)
from vedro.events import ArgParsedEvent, ArgParseEvent, ConfigLoadedEvent, ScenarioRunEvent
from vedro.plugins.director import Director, DirectorPlugin
from vedro.plugins.director.rich import RichPrinter

from vedro_gitlab_reporter import GitlabCollapsableMode, GitlabReporter, GitlabReporterPlugin


@pytest.fixture()
def dispatcher() -> Dispatcher:
    return Dispatcher()


@pytest.fixture()
def printer_() -> Mock:
    return Mock(RichPrinter)


@pytest.fixture()
def director(dispatcher: Dispatcher) -> DirectorPlugin:
    director = DirectorPlugin(Director)
    director.subscribe(dispatcher)
    return director


@pytest.fixture()
def gitlab_reporter(dispatcher: Dispatcher,
                    director: DirectorPlugin, printer_: Mock) -> GitlabReporterPlugin:
    reporter = GitlabReporterPlugin(GitlabReporter, printer_factory=lambda: printer_)
    reporter.subscribe(dispatcher)
    return reporter


async def fire_arg_parsed_event(dispatcher: Dispatcher, *,
                                collapsable_mode: Union[GitlabCollapsableMode, None] = None,
                                tb_show_internal_calls: bool =
                                GitlabReporter.tb_show_internal_calls,
                                tb_show_locals: bool =
                                GitlabReporter.tb_show_locals) -> None:
    await dispatcher.fire(ConfigLoadedEvent(Path(), Config))

    arg_parse_event = ArgParseEvent(ArgumentParser())
    await dispatcher.fire(arg_parse_event)

    namespace = Namespace(gitlab_collapsable=collapsable_mode,
                          gitlab_tb_show_internal_calls=tb_show_internal_calls,
                          gitlab_tb_show_locals=tb_show_locals)
    arg_parsed_event = ArgParsedEvent(namespace)
    await dispatcher.fire(arg_parsed_event)


async def fire_scenario_run_event(dispatcher: Dispatcher,
                                  scenario_result: Optional[ScenarioResult] = None
                                  ) -> ScenarioResult:
    if scenario_result is None:
        scenario_result = make_scenario_result()
    scenario_run_event = ScenarioRunEvent(scenario_result)
    await dispatcher.fire(scenario_run_event)
    return scenario_result


def make_vstep(name: Optional[str] = None) -> VirtualStep:
    def step():
        pass
    step.__name__ = name or f"step_{monotonic_ns()}"
    return VirtualStep(step)


def make_vscenario() -> VirtualScenario:
    class _Scenario(Scenario):
        __file__ = Path(f"scenario_{monotonic_ns()}.py").absolute()

    return VirtualScenario(_Scenario, steps=[])


def make_step_result(vstep: Optional[VirtualStep] = None) -> StepResult:
    return StepResult(vstep or make_vstep())


def make_scenario_result(vscenario: Optional[VirtualScenario] = None,
                         extra_details: str = None) -> ScenarioResult:
    scenario_result = ScenarioResult(vscenario or make_vscenario())
    if extra_details:
        scenario_result.add_extra_details(extra_details)
    return scenario_result


def make_aggregated_result(scenario_result: Optional[ScenarioResult] = None) -> AggregatedResult:
    if scenario_result is None:
        scenario_result = make_scenario_result()
    return AggregatedResult.from_existing(scenario_result, [scenario_result])


def make_exc_info(exc_val: Exception) -> ExcInfo:
    try:
        raise exc_val
    except type(exc_val):
        *_, traceback = sys.exc_info()
    return ExcInfo(type(exc_val), exc_val, cast(TracebackType, traceback))


@contextmanager
def patch_uuid(uuid: Optional[str] = None):
    if uuid is None:
        uuid = str(uuid4())
    with patch("uuid.uuid4", Mock(return_value=uuid)):
        yield uuid
