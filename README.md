# Vedro GitLab Reporter

[![Codecov](https://img.shields.io/codecov/c/github/nikitanovosibirsk/vedro-gitlab-reporter/master.svg?style=flat-square)](https://codecov.io/gh/nikitanovosibirsk/vedro-gitlab-reporter)
[![PyPI](https://img.shields.io/pypi/v/vedro-gitlab-reporter.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-gitlab-reporter/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/vedro-gitlab-reporter?style=flat-square)](https://pypi.python.org/pypi/vedro-gitlab-reporter/)
[![Python Version](https://img.shields.io/pypi/pyversions/vedro-gitlab-reporter.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-gitlab-reporter/)

GitLab (>=12.0) reporter with [collapsable sections](https://docs.gitlab.com/ee/ci/jobs/#custom-collapsible-sections) for [Vedro](https://github.com/nikitanovosibirsk/vedro) framework

## Installation

```shell
$ pip3 install vedro-gitlab-reporter
```

```python
# ./bootstrap.py
import vedro
from vedro_gitlab_reporter import GitlabReporter

vedro.run(plugins=[GitlabReporter()])
```

```shell
$ python3 bootstrap.py -r gitlab -vvv
```

## Documentation

### Verbose Levels

`-v` — show exception and collapsable steps

`-vv` — show exception, steps and collapsable variables

`-vvv` — show exception, steps and collapsable scope
