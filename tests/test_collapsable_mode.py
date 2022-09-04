import pytest
from baby_steps import then, when

from vedro_gitlab_reporter import GitlabCollapsableMode


@pytest.mark.parametrize(("mode", "text"), [
    (GitlabCollapsableMode.STEPS, "steps"),
    (GitlabCollapsableMode.VARS, "vars"),
    (GitlabCollapsableMode.SCOPE, "scope"),
])
def test_collapsable_mode(mode: GitlabCollapsableMode, text: str):
    with when:
        res = str(mode)

    with then:
        assert res == text
