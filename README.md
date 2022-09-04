# Vedro GitLab Reporter

[![Codecov](https://img.shields.io/codecov/c/github/nikitanovosibirsk/vedro-gitlab-reporter/master.svg?style=flat-square)](https://codecov.io/gh/nikitanovosibirsk/vedro-gitlab-reporter)
[![PyPI](https://img.shields.io/pypi/v/vedro-gitlab-reporter.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-gitlab-reporter/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/vedro-gitlab-reporter?style=flat-square)](https://pypi.python.org/pypi/vedro-gitlab-reporter/)
[![Python Version](https://img.shields.io/pypi/pyversions/vedro-gitlab-reporter.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-gitlab-reporter/)

GitLab (>=12.0) reporter with [collapsable sections](https://docs.gitlab.com/ee/ci/jobs/#custom-collapsible-sections) for [Vedro](https://github.com/nikitanovosibirsk/vedro) framework

## Installation

### 1. Install package

```shell
$ pip3 install vedro-gitlab-reporter
```

### 2. Enable plugin

```python
# ./vedro.cfg.py
import vedro
import vedro_gitlab_reporter as gitlab_reporter

class Config(vedro.Config):

    class Plugins(vedro.Config.Plugins):

        class GitlabReporter(gitlab_reporter.GitlabReporter):
            enabled = True
```

## Usage

### Run tests

```shell
$ vedro run -r gitlab --gitlab-collapsable steps
```

## Documentation

`--gitlab-collapsable=<mode>`

| Mode  | Description                                     |
| ----- | ----------------------------------------------- |
| steps | Show exception and collapsable steps            |
| vars  | Show exception, steps and collapsable variables |
| scope | Show exception, steps and collapsable scope     |
