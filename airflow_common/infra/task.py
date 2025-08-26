from typing import Optional, Type

from airflow_pydantic import BashTask, BashTaskArgs, CallablePath, SSHTask, SSHTaskArgs
from airflow_pydantic.airflow import BashOperator, SSHOperator
from pydantic import Field, field_validator

__all__ = (
    "JournalctlClean",
    "JournalctlCleanSSH",
    "JournalctlCleanOperator",
    "JournalctlCleanOperatorArgs",
    "JournalctlCleanSSHOperatorArgs",
    "JournalctlCleanSSHOperator",
    "JournalctlCleanTask",
    "JournalctlCleanTaskArgs",
    "JournalctlCleanSSHTask",
    "JournalctlCleanSSHTaskArgs",
)


def clean_journalctl(sudo: Optional[bool] = True, days: Optional[int] = 2):
    days = days or 2
    cmd = f"sudo journalctl --vacuum-time={days}d" if sudo else f"journalctl --vacuum-time={days}d"
    return cmd


class JournalctlClean(BashOperator):
    def __init__(self, sudo: Optional[bool] = True, days: Optional[int] = 2, **kwargs):
        if "bash_command" in kwargs:
            raise ValueError("JournalctlClean does not accept 'bash_command' as an argument.")
        super().__init__(bash_command=clean_journalctl(sudo=sudo, days=days), **kwargs)


class JournalctlCleanSSH(SSHOperator):
    def __init__(self, sudo: Optional[bool] = True, days: Optional[int] = 2, **kwargs):
        if "command" in kwargs:
            raise ValueError("JournalctlCleanSSH does not accept 'command' as an argument.")
        super().__init__(command=clean_journalctl(sudo=sudo, days=days), **kwargs)


class JournalctlCleanTaskArgs(BashTaskArgs):
    sudo: Optional[bool] = Field(default=True)
    days: Optional[int] = Field(default=2)


class JournalctlCleanSSHTaskArgs(SSHTaskArgs):
    sudo: Optional[bool] = Field(default=True)
    days: Optional[int] = Field(default=2)


# Alias
JournalctlCleanOperatorArgs = JournalctlCleanTaskArgs
JournalctlCleanSSHOperatorArgs = JournalctlCleanSSHTaskArgs


class JournalctlCleanTask(BashTask, JournalctlCleanTaskArgs):
    operator: CallablePath = Field(default="airflow_common.JournalctlClean", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Type) -> Type:
        if v is not JournalctlClean:
            raise ValueError(f"operator must be 'airflow_common.JournalctlClean', got: {v}")
        return v


class JournalctlCleanSSHTask(SSHTask, JournalctlCleanSSHTaskArgs):
    operator: CallablePath = Field(default="airflow_common.JournalctlCleanSSH", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Type) -> Type:
        if v is not JournalctlCleanSSH:
            raise ValueError(f"operator must be 'airflow_common.JournalctlCleanSSH', got: {v}")
        return v


# Alias
JournalctlCleanOperator = JournalctlCleanTask
JournalctlCleanSSHOperator = JournalctlCleanSSHTask
