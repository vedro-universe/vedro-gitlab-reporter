import operator
import uuid
from functools import reduce
from typing import Callable, Dict, List, Set, Type, Union

from vedro.core import Dispatcher, PluginConfig, ScenarioResult
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    CleanupEvent,
    ScenarioReportedEvent,
    ScenarioRunEvent,
    StartupEvent,
    StepFailedEvent,
    StepPassedEvent,
)
from vedro.plugins.director import DirectorInitEvent, Reporter
from vedro.plugins.director.rich import RichPrinter

from ._collapsable_mode import GitlabCollapsableMode

__all__ = ("GitlabReporter", "GitlabReporterPlugin",)


class GitlabReporterPlugin(Reporter):
    def __init__(self, config: Type["GitlabReporter"], *,
                 printer_factory: Callable[[], RichPrinter] = RichPrinter) -> None:
        super().__init__(config)
        self._printer = printer_factory()

        self._tb_show_internal_calls = config.tb_show_internal_calls
        self._tb_show_locals = config.tb_show_locals
        self._tb_max_frames = config.tb_max_frames
        self._collapsable_mode: Union[GitlabCollapsableMode, None] = None

        self._namespace: Union[str, None] = None
        self._scenario_result: Union[ScenarioResult, None] = None
        self._scenario_steps: List[Dict[str, Set[str]]] = []

    def subscribe(self, dispatcher: Dispatcher) -> None:
        super().subscribe(dispatcher)
        dispatcher.listen(DirectorInitEvent, lambda e: e.director.register("gitlab", self))

    def on_chosen(self) -> None:
        assert isinstance(self._dispatcher, Dispatcher)
        self._dispatcher.listen(ArgParseEvent, self.on_arg_parse) \
                        .listen(ArgParsedEvent, self.on_arg_parsed) \
                        .listen(StartupEvent, self.on_startup) \
                        .listen(ScenarioRunEvent, self.on_scenario_run) \
                        .listen(StepPassedEvent, self.on_step_end) \
                        .listen(StepFailedEvent, self.on_step_end) \
                        .listen(ScenarioReportedEvent, self.on_scenario_reported) \
                        .listen(CleanupEvent, self.on_cleanup)

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        group = event.arg_parser.add_argument_group("GitLab Reporter")

        group.add_argument("--gitlab-collapsable",
                           type=GitlabCollapsableMode,
                           choices=[x for x in GitlabCollapsableMode],
                           help="Choose collapsable mode")
        group.add_argument("--gitlab-tb-show-internal-calls",
                           action="store_true",
                           default=self._tb_show_internal_calls,
                           help="Show internal calls in the traceback output")
        group.add_argument("--gitlab-tb-show-locals",
                           action="store_true",
                           default=self._tb_show_locals,
                           help="Show local variables in the traceback output")

    def on_arg_parsed(self, event: ArgParsedEvent) -> None:
        self._collapsable_mode = event.args.gitlab_collapsable
        self._tb_show_internal_calls = event.args.gitlab_tb_show_internal_calls
        self._tb_show_locals = event.args.gitlab_tb_show_locals

    def on_startup(self, event: StartupEvent) -> None:
        self._printer.print_header()

    def on_scenario_run(self, event: ScenarioRunEvent) -> None:
        namespace = event.scenario_result.scenario.namespace
        if namespace != self._namespace:
            self._namespace = namespace
            self._printer.print_namespace(namespace)

        unique_id = event.scenario_result.scenario.unique_id
        if self._scenario_result is None or self._scenario_result.scenario.unique_id != unique_id:
            self._scenario_steps = []
        self._scenario_steps.append({})
        self._scenario_result = event.scenario_result

    def on_step_end(self, event: Union[StepPassedEvent, StepFailedEvent]) -> None:
        assert isinstance(self._scenario_result, ScenarioResult)

        scenario_steps = self._scenario_steps[-1]
        step_scope: Set[str] = set(self._scenario_result.scope.keys())
        prev_scope: Set[str] = reduce(operator.or_, scenario_steps.values(), set())
        scenario_steps[event.step_result.step_name] = step_scope - prev_scope

    def _print_scenario_result(self, scenario_result: ScenarioResult, *,
                               index: int = 0, prefix: str = "") -> None:
        if scenario_result.is_passed():
            self._print_scenario_passed(scenario_result, index=index, prefix=prefix)
        elif scenario_result.is_failed():
            self._print_scenario_failed(scenario_result, index=index, prefix=prefix)

    def _print_scenario_passed(self, scenario_result: ScenarioResult, *,
                               index: int = 0, prefix: str = "") -> None:
        self._printer.print_scenario_subject(scenario_result.scenario.subject,
                                             scenario_result.status,
                                             elapsed=scenario_result.elapsed,
                                             prefix=prefix)

    def _print_scenario_failed(self, scenario_result: ScenarioResult, *,
                               index: int = 0, prefix: str = "") -> None:
        self._printer.print_scenario_subject(scenario_result.scenario.subject,
                                             scenario_result.status,
                                             elapsed=scenario_result.elapsed,
                                             prefix=prefix)

        if self._collapsable_mode == GitlabCollapsableMode.STEPS:
            prefix = self._prefix_to_indent(prefix, indent=2)
            self._print_collapsable_steps(scenario_result, index=index, prefix=prefix)
            self._print_exceptions(scenario_result)

        elif self._collapsable_mode == GitlabCollapsableMode.VARS:
            prefix = self._prefix_to_indent(prefix, indent=2)
            self._print_steps_with_collapsable_vars(scenario_result, index=index, prefix=prefix)
            self._print_exceptions(scenario_result)

        elif self._collapsable_mode == GitlabCollapsableMode.SCOPE:
            prefix = self._prefix_to_indent(prefix, indent=2)
            self._print_steps(scenario_result, prefix=prefix)
            self._print_exceptions(scenario_result)
            self._print_collapsable_scope(scenario_result)

    def on_scenario_reported(self, event: ScenarioReportedEvent) -> None:
        aggregated_result = event.aggregated_result
        rescheduled = len(aggregated_result.scenario_results)
        if rescheduled == 1:
            self._print_scenario_result(aggregated_result, prefix=" ")
            return

        self._printer.print_scenario_subject(aggregated_result.scenario.subject,
                                             aggregated_result.status, elapsed=None, prefix=" ")
        for index, scenario_result in enumerate(aggregated_result.scenario_results):
            prefix = f" │\n ├─[{index+1}/{rescheduled}] "
            self._print_scenario_result(scenario_result, index=index, prefix=prefix)

        self._printer.print_empty_line()

    def on_cleanup(self, event: CleanupEvent) -> None:
        self._printer.print_empty_line()
        self._printer.print_report_summary(event.report.summary)
        self._printer.print_report_stats(total=event.report.total,
                                         passed=event.report.passed,
                                         failed=event.report.failed,
                                         skipped=event.report.skipped,
                                         elapsed=event.report.elapsed)

    def _print_section_start(self, name: str, started_at: int = 0, *,
                             is_collapsed: bool = True) -> None:
        collapsed = "true" if is_collapsed else "false"
        output = f'\033[0Ksection_start:{started_at}:{name}[collapsed={collapsed}]\r\033[0K'
        self._printer.console.file.write(output)

    def _print_section_end(self, name: str, ended_at: int = 0) -> None:
        output = f'\033[0Ksection_end:{ended_at}:{name}\r\033[0K'
        self._printer.console.file.write(output)

    def _prefix_to_indent(self, prefix: str, indent: int = 0) -> str:
        last_line = prefix.split("\n")[-1]
        return (len(last_line) + indent) * " "

    def _print_steps(self, scenario_result: ScenarioResult, *, prefix: str = "") -> None:
        for step_result in scenario_result.step_results:
            self._printer.print_step_name(step_result.step_name, step_result.status,
                                          elapsed=step_result.elapsed, prefix=prefix)

    def _print_collapsable_steps(self, scenario_result: ScenarioResult, *,
                                 index: int = 0, prefix: str = "") -> None:
        for step_result in scenario_result.step_results:
            section_name = str(uuid.uuid4())
            started_at = int(step_result.started_at) if step_result.started_at else 0
            self._print_section_start(section_name, started_at)

            self._printer.print_step_name(step_result.step_name, step_result.status,
                                          elapsed=step_result.elapsed, prefix=prefix)

            scenario_steps = self._scenario_steps[index]
            for key, val in scenario_result.scope.items():
                if key not in scenario_steps[step_result.step_name]:
                    continue
                self._printer.print_scope_key(key, indent=len(prefix) + 2, line_break=True)
                self._printer.print_scope_val(self._printer.pretty_format(val))

            ended_at = int(step_result.ended_at) if step_result.ended_at else 0
            self._print_section_end(section_name, ended_at)

    def _print_steps_with_collapsable_vars(self, scenario_result: ScenarioResult, *,
                                           index: int = 0, prefix: str = "") -> None:
        for step_result in scenario_result.step_results:
            self._printer.print_step_name(step_result.step_name, step_result.status,
                                          elapsed=step_result.elapsed, prefix=prefix)

            scenario_steps = self._scenario_steps[index]
            for key, val in scenario_result.scope.items():
                if key not in scenario_steps[step_result.step_name]:
                    continue
                section_name = str(uuid.uuid4())
                self._print_section_start(section_name)

                self._printer.print_scope_key(key, indent=len(prefix) + 2, line_break=True)
                self._printer.print_scope_val(self._printer.pretty_format(val))

                self._print_section_end(section_name)

    def _print_exceptions(self, scenario_result: ScenarioResult) -> None:
        for step_result in scenario_result.step_results:
            if step_result.exc_info is None:
                continue
            self._printer.print_pretty_exception(step_result.exc_info,
                                                 max_frames=self._tb_max_frames,
                                                 show_locals=self._tb_show_locals,
                                                 show_internal_calls=self._tb_show_internal_calls)

    def _print_collapsable_scope(self, scenario_result: ScenarioResult) -> None:
        section_name = str(uuid.uuid4())
        self._print_section_start(section_name)
        self._printer.print_scope(scenario_result.scope)
        self._print_section_end(section_name)


class GitlabReporter(PluginConfig):
    plugin = GitlabReporterPlugin

    # Show internal calls in the traceback output
    tb_show_internal_calls: bool = False

    # Show local variables in the traceback output
    tb_show_locals: bool = False

    # Max stack trace entries to show (min=4)
    tb_max_frames: int = 8
