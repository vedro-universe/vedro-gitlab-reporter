from vedro.plugins.director import Reporter

from vedro_gitlab_reporter import GitlabReporter


def test_gitlab_reporter():
    reporter = GitlabReporter()
    assert isinstance(reporter, Reporter)
