from typing import Literal, Optional, Type

from airflow_pydantic import BashTask, BashTaskArgs, CallablePath, SSHTask, SSHTaskArgs
from airflow_pydantic.airflow import BashOperator, SSHOperator
from pydantic import Field, field_validator

__all__ = (
    "Systemctl",
    "SystemctlSSH",
    "SystemctlOperator",
    "SystemctlOperatorArgs",
    "SystemctlSSHOperatorArgs",
    "SystemctlSSHOperator",
    "SystemctlTask",
    "SystemctlTaskArgs",
    "SystemctlSSHTask",
    "SystemctlSSHTaskArgs",
    "SystemctlAction",
    "systemctl_command",
)

SystemctlAction = Literal["start", "stop", "enable", "disable", "restart", "status"]


def systemctl_command(service: str, action: SystemctlAction = "restart", sudo: Optional[bool] = True) -> str:
    """Generate a systemctl command."""
    cmd = f"systemctl {action} {service}"
    if sudo:
        cmd = f"sudo {cmd}"
    return cmd


class Systemctl(BashOperator):
    _original = "airflow_common.infra.systemctl.Systemctl"

    def __init__(
        self,
        service: str,
        action: SystemctlAction = "restart",
        sudo: Optional[bool] = True,
        **kwargs,
    ):
        if "bash_command" in kwargs:
            raise ValueError("Systemctl does not accept 'bash_command' as an argument.")
        super().__init__(bash_command=systemctl_command(service=service, action=action, sudo=sudo), **kwargs)


class SystemctlSSH(SSHOperator):
    _original = "airflow_common.infra.systemctl.SystemctlSSH"

    def __init__(
        self,
        service: str,
        action: SystemctlAction = "restart",
        sudo: Optional[bool] = True,
        **kwargs,
    ):
        if "command" in kwargs:
            raise ValueError("SystemctlSSH does not accept 'command' as an argument.")
        super().__init__(command=systemctl_command(service=service, action=action, sudo=sudo), **kwargs)


class SystemctlTaskArgs(BashTaskArgs):
    service: str = Field(...)
    action: SystemctlAction = Field(default="restart")
    sudo: Optional[bool] = Field(default=True)


class SystemctlSSHTaskArgs(SSHTaskArgs):
    service: str = Field(...)
    action: SystemctlAction = Field(default="restart")
    sudo: Optional[bool] = Field(default=True)


# Alias
SystemctlOperatorArgs = SystemctlTaskArgs
SystemctlSSHOperatorArgs = SystemctlSSHTaskArgs


class SystemctlTask(BashTask, SystemctlTaskArgs):
    operator: CallablePath = Field(default="airflow_common.Systemctl", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Type) -> Type:
        if v is not Systemctl:
            raise ValueError(f"operator must be 'airflow_common.Systemctl', got: {v}")
        return v


class SystemctlSSHTask(SSHTask, SystemctlSSHTaskArgs):
    operator: CallablePath = Field(default="airflow_common.SystemctlSSH", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Type) -> Type:
        if v is not SystemctlSSH:
            raise ValueError(f"operator must be 'airflow_common.SystemctlSSH', got: {v}")
        return v


# Alias
SystemctlOperator = SystemctlTask
SystemctlSSHOperator = SystemctlSSHTask
