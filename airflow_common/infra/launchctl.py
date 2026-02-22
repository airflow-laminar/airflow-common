from typing import Literal

from airflow_pydantic import BashTask, BashTaskArgs, CallablePath, SSHTask, SSHTaskArgs
from airflow_pydantic.airflow import BashOperator, SSHOperator
from pydantic import Field, field_validator

__all__ = (
    "Lunchy",
    "LunchyAction",
    "LunchyOperator",
    "LunchyOperatorArgs",
    "LunchySSH",
    "LunchySSHOperator",
    "LunchySSHOperatorArgs",
    "LunchySSHTask",
    "LunchySSHTaskArgs",
    "LunchyTask",
    "LunchyTaskArgs",
    "lunchy_command",
)

LunchyAction = Literal["start", "stop", "restart", "status", "list"]


def lunchy_command(service: str, action: LunchyAction = "restart", sudo: bool | None = False) -> str:
    """Generate a lunchy command for macOS launchctl management.

    Lunchy is a friendly wrapper around launchctl for managing launchd agents/daemons.
    """
    cmd = f"lunchy {action} {service}"
    if sudo:
        cmd = f"sudo {cmd}"
    return cmd


class Lunchy(BashOperator):
    _original = "airflow_common.infra.launchctl.Lunchy"

    def __init__(
        self,
        service: str,
        action: LunchyAction = "restart",
        sudo: bool | None = False,
        **kwargs,
    ):
        if "bash_command" in kwargs:
            raise ValueError("Lunchy does not accept 'bash_command' as an argument.")
        super().__init__(bash_command=lunchy_command(service=service, action=action, sudo=sudo), **kwargs)


class LunchySSH(SSHOperator):
    _original = "airflow_common.infra.launchctl.LunchySSH"

    def __init__(
        self,
        service: str,
        action: LunchyAction = "restart",
        sudo: bool | None = False,
        **kwargs,
    ):
        if "command" in kwargs:
            raise ValueError("LunchySSH does not accept 'command' as an argument.")
        super().__init__(command=lunchy_command(service=service, action=action, sudo=sudo), **kwargs)


class LunchyTaskArgs(BashTaskArgs):
    service: str = Field(...)
    action: LunchyAction = Field(default="restart")
    sudo: bool | None = Field(default=False)


class LunchySSHTaskArgs(SSHTaskArgs):
    service: str = Field(...)
    action: LunchyAction = Field(default="restart")
    sudo: bool | None = Field(default=False)


# Alias
LunchyOperatorArgs = LunchyTaskArgs
LunchySSHOperatorArgs = LunchySSHTaskArgs


class LunchyTask(BashTask, LunchyTaskArgs):
    operator: CallablePath = Field(default="airflow_common.Lunchy", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: type) -> type:
        if v is not Lunchy:
            raise ValueError(f"operator must be 'airflow_common.Lunchy', got: {v}")
        return v


class LunchySSHTask(SSHTask, LunchySSHTaskArgs):
    operator: CallablePath = Field(default="airflow_common.LunchySSH", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: type) -> type:
        if v is not LunchySSH:
            raise ValueError(f"operator must be 'airflow_common.LunchySSH', got: {v}")
        return v


# Alias
LunchyOperator = LunchyTask
LunchySSHOperator = LunchySSHTask
