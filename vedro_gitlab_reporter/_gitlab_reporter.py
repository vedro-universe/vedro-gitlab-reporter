from enum import Enum
from typing import Callable, Type, Union

from vedro.core import Dispatcher, PluginConfig, ScenarioResult
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    CleanupEvent,
    ScenarioReportedEvent,
    ScenarioRunEvent,
    StartupEvent,
)
from vedro.plugins.director import DirectorInitEvent, Reporter
from vedro.plugins.director.rich import RichPrinter

__all__ = ("GitlabReporter", "GitlabReporterPlugin", "GitlabCollapsableMode",)


class GitlabCollapsableMode(Enum):
    STEPS = "steps"
    VARS = "vars"
    SCOPE = "scope"

    def __str__(self) -> str:
        return self.value


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

    def subscribe(self, dispatcher: Dispatcher) -> None:
        super().subscribe(dispatcher)
        dispatcher.listen(DirectorInitEvent, lambda e: e.director.register("gitlab", self))

    def on_chosen(self) -> None:
        assert isinstance(self._dispatcher, Dispatcher)
        self._dispatcher.listen(ArgParseEvent, self.on_arg_parse) \
                        .listen(ArgParsedEvent, self.on_arg_parsed) \
                        .listen(StartupEvent, self.on_startup) \
                        .listen(ScenarioRunEvent, self.on_scenario_run) \
                        .listen(ScenarioReportedEvent, self.on_scenario_reported) \
                        .listen(CleanupEvent, self.on_cleanup)

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        group = event.arg_parser.add_argument_group("GitLab Reporter")

        group.add_argument("--gitlab-collapsable",
                           type=GitlabCollapsableMode,
                           choices=[x for x in GitlabCollapsableMode],
                           help="Choose collapsable mode")
        group.add_argument("--tb-show-internal-calls",
                           action="store_true",
                           default=self._tb_show_internal_calls,
                           help="Show internal calls in the traceback output")
        group.add_argument("--tb-show-locals",
                           action="store_true",
                           default=self._tb_show_locals,
                           help="Show local variables in the traceback output")

    def on_arg_parsed(self, event: ArgParsedEvent) -> None:
        self._collapsable_mode = event.args.gitlab_collapsable
        self._tb_show_internal_calls = event.args.tb_show_internal_calls
        self._tb_show_locals = event.args.tb_show_locals

    def on_startup(self, event: StartupEvent) -> None:
        self._printer.print_header()

    def on_scenario_run(self, event: ScenarioRunEvent) -> None:
        namespace = event.scenario_result.scenario.namespace
        if namespace != self._namespace:
            self._namespace = namespace
            self._printer.print_namespace(namespace)

    def _print_scenario_passed(self, scenario_result: ScenarioResult, *, prefix: str = "") -> None:
        self._printer.print_scenario_subject(scenario_result.scenario.subject,
                                             scenario_result.status,
                                             elapsed=scenario_result.elapsed,
                                             prefix=prefix)

    def _print_scenario_result(self, scenario_result: ScenarioResult, *, prefix: str = "") -> None:
        if scenario_result.is_passed():
            self._print_scenario_passed(scenario_result, prefix=prefix)
        elif scenario_result.is_failed():
            self._print_scenario_failed(scenario_result, prefix=prefix)

    def _print_section_start(self, name: str, started_at: int = 0, *,
                             is_collapsed: bool = True) -> None:
        collapsed = "true" if is_collapsed else "false"
        output = f'\033[0Ksection_start:{started_at}:{name}[collapsed={collapsed}]\r\033[0K'
        self._printer.console.file.write(output)

    def _print_section_end(self, name: str, ended_at: int = 0) -> None:
        output = f'\033[0Ksection_end:{ended_at}:{name}\r\033[0K'
        self._printer.console.file.write(output)

    def _print_scenario_failed(self, scenario_result: ScenarioResult, *, prefix: str = "") -> None:
        self._printer.print_scenario_subject(scenario_result.scenario.subject,
                                             scenario_result.status,
                                             elapsed=scenario_result.elapsed,
                                             prefix=prefix)

    def on_scenario_reported(self, event: ScenarioReportedEvent) -> None:
        aggregated_result = event.aggregated_result
        rescheduled = len(aggregated_result.scenario_results)
        if rescheduled == 1:
            self._print_scenario_result(aggregated_result, prefix=" ")
            return

        self._printer.print_scenario_subject(aggregated_result.scenario.subject,
                                             aggregated_result.status, elapsed=None, prefix=" ")
        for index, scenario_result in enumerate(aggregated_result.scenario_results, start=1):
            prefix = f" │\n ├─[{index}/{rescheduled}] "
            self._print_scenario_result(scenario_result, prefix=prefix)

        self._printer.print_empty_line()

    def on_cleanup(self, event: CleanupEvent) -> None:
        self._printer.print_empty_line()
        self._printer.print_report_summary(event.report.summary)
        self._printer.print_report_stats(total=event.report.total,
                                         passed=event.report.passed,
                                         failed=event.report.failed,
                                         skipped=event.report.skipped,
                                         elapsed=event.report.elapsed)


class GitlabReporter(PluginConfig):
    plugin = GitlabReporterPlugin

    # Show internal calls in the traceback output
    tb_show_internal_calls: bool = False

    # Show local variables in the traceback output
    # Available if tb_pretty is True
    tb_show_locals: bool = False

    # Max stack trace entries to show (min=4)
    tb_max_frames: int = 8
