from typing import Optional, Type

from airflow_pydantic import BashTask, BashTaskArgs, CallablePath, SSHTask, SSHTaskArgs
from airflow_pydantic.airflow import BashOperator, SSHOperator
from pydantic import Field, field_validator

__all__ = (
    "Reboot",
    "RebootSSH",
    "RebootOperator",
    "RebootOperatorArgs",
    "RebootSSHOperatorArgs",
    "RebootSSHOperator",
    "RebootTask",
    "RebootTaskArgs",
    "RebootSSHTask",
    "RebootSSHTaskArgs",
    "reboot_command",
)


def reboot_command(sudo: Optional[bool] = True, delay_minutes: Optional[int] = None) -> str:
    """Generate a reboot command.

    Args:
        sudo: Whether to use sudo
        delay_minutes: If provided, schedule reboot using 'at' command after this many minutes
    """
    if delay_minutes is not None:
        # Use 'at' command to schedule reboot
        reboot_cmd = "sudo reboot now" if sudo else "reboot now"
        return f"echo '{reboot_cmd}' | at now + {delay_minutes} minutes"
    else:
        if sudo:
            return "sudo reboot now"
        return "reboot now"


class Reboot(BashOperator):
    _original = "airflow_common.infra.reboot.Reboot"

    def __init__(
        self,
        sudo: Optional[bool] = True,
        delay_minutes: Optional[int] = None,
        **kwargs,
    ):
        if "bash_command" in kwargs:
            raise ValueError("Reboot does not accept 'bash_command' as an argument.")
        super().__init__(bash_command=reboot_command(sudo=sudo, delay_minutes=delay_minutes), **kwargs)


class RebootSSH(SSHOperator):
    _original = "airflow_common.infra.reboot.RebootSSH"

    def __init__(
        self,
        sudo: Optional[bool] = True,
        delay_minutes: Optional[int] = None,
        **kwargs,
    ):
        if "command" in kwargs:
            raise ValueError("RebootSSH does not accept 'command' as an argument.")
        super().__init__(command=reboot_command(sudo=sudo, delay_minutes=delay_minutes), **kwargs)


class RebootTaskArgs(BashTaskArgs):
    sudo: Optional[bool] = Field(default=True)
    delay_minutes: Optional[int] = Field(default=None, description="Delay reboot by N minutes using 'at' command")


class RebootSSHTaskArgs(SSHTaskArgs):
    sudo: Optional[bool] = Field(default=True)
    delay_minutes: Optional[int] = Field(default=None, description="Delay reboot by N minutes using 'at' command")


# Alias
RebootOperatorArgs = RebootTaskArgs
RebootSSHOperatorArgs = RebootSSHTaskArgs


class RebootTask(BashTask, RebootTaskArgs):
    operator: CallablePath = Field(default="airflow_common.Reboot", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Type) -> Type:
        if v is not Reboot:
            raise ValueError(f"operator must be 'airflow_common.Reboot', got: {v}")
        return v


class RebootSSHTask(SSHTask, RebootSSHTaskArgs):
    operator: CallablePath = Field(default="airflow_common.RebootSSH", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Type) -> Type:
        if v is not RebootSSH:
            raise ValueError(f"operator must be 'airflow_common.RebootSSH', got: {v}")
        return v


# Alias
RebootOperator = RebootTask
RebootSSHOperator = RebootSSHTask
