# Vedro GitLab Reporter

[![Codecov](https://img.shields.io/codecov/c/github/vedro-universe/vedro-gitlab-reporter/master.svg?style=flat-square)](https://codecov.io/gh/vedro-universe/vedro-gitlab-reporter)
[![PyPI](https://img.shields.io/pypi/v/vedro-gitlab-reporter.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-gitlab-reporter/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/vedro-gitlab-reporter?style=flat-square)](https://pypi.python.org/pypi/vedro-gitlab-reporter/)
[![Python Version](https://img.shields.io/pypi/pyversions/vedro-gitlab-reporter.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-gitlab-reporter/)

GitLab (>=12.0) reporter with [collapsable sections](https://docs.gitlab.com/ee/ci/jobs/#custom-collapsible-sections) for [Vedro](https://vedro.io/) framework

## Installation

<details open>
<summary>Quick</summary>
<p>

For a quick installation, you can use a plugin manager as follows:

```shell
$ vedro plugin install vedro-gitlab-reporter
```

</p>
</details>

<details>
<summary>Manual</summary>
<p>

To install manually, follow these steps:

1. Install the package using pip:

```shell
$ pip3 install vedro-gitlab-reporter
```

2. Next, activate the plugin in your `vedro.cfg.py` configuration file:

```python
# ./vedro.cfg.py
import vedro
import vedro_gitlab_reporter

class Config(vedro.Config):

    class Plugins(vedro.Config.Plugins):

        class GitlabReporter(vedro_gitlab_reporter.GitlabReporter):
            enabled = True
```

</p>
</details>

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
