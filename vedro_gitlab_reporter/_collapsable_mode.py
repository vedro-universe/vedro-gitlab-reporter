from enum import Enum

__all__ = ("GitlabCollapsableMode",)


class GitlabCollapsableMode(Enum):
    STEPS = "steps"
    VARS = "vars"
    SCOPE = "scope"

    def __str__(self) -> str:
        return self.value
