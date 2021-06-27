# Vedro GitLab Reporter

[GitLab](https://gitlab.com) (>=12.0) reporter with collapsable sections.

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
