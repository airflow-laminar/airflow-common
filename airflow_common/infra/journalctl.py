from airflow_pydantic import BashTask, BashTaskArgs, CallablePath, SSHTask, SSHTaskArgs
from airflow_pydantic.airflow import BashOperator, SSHOperator
from pydantic import Field, field_validator

__all__ = (
    "JournalctlClean",
    "JournalctlCleanOperator",
    "JournalctlCleanOperatorArgs",
    "JournalctlCleanSSH",
    "JournalctlCleanSSHOperator",
    "JournalctlCleanSSHOperatorArgs",
    "JournalctlCleanSSHTask",
    "JournalctlCleanSSHTaskArgs",
    "JournalctlCleanTask",
    "JournalctlCleanTaskArgs",
    "clean_journalctl",
)


def clean_journalctl(sudo: bool | None = True, days: int | None = 2):
    days = days or 2
    return f"sudo journalctl --vacuum-time={days}d" if sudo else f"journalctl --vacuum-time={days}d"


class JournalctlClean(BashOperator):
    _original = "airflow_common.infra.journalctl.JournalctlClean"

    def __init__(self, sudo: bool | None = True, days: int | None = 2, **kwargs):
        if "bash_command" in kwargs:
            raise ValueError("JournalctlClean does not accept 'bash_command' as an argument.")
        super().__init__(bash_command=clean_journalctl(sudo=sudo, days=days), **kwargs)


class JournalctlCleanSSH(SSHOperator):
    _original = "airflow_common.infra.journalctl.JournalctlCleanSSH"

    def __init__(self, sudo: bool | None = True, days: int | None = 2, **kwargs):
        if "command" in kwargs:
            raise ValueError("JournalctlCleanSSH does not accept 'command' as an argument.")
        super().__init__(command=clean_journalctl(sudo=sudo, days=days), **kwargs)


class JournalctlCleanTaskArgs(BashTaskArgs):
    sudo: bool | None = Field(default=True)
    days: int | None = Field(default=2)


class JournalctlCleanSSHTaskArgs(SSHTaskArgs):
    sudo: bool | None = Field(default=True)
    days: int | None = Field(default=2)


# Alias
JournalctlCleanOperatorArgs = JournalctlCleanTaskArgs
JournalctlCleanSSHOperatorArgs = JournalctlCleanSSHTaskArgs


class JournalctlCleanTask(BashTask, JournalctlCleanTaskArgs):
    operator: CallablePath = Field(default="airflow_common.JournalctlClean", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: type) -> type:
        if v is not JournalctlClean:
            raise ValueError(f"operator must be 'airflow_common.JournalctlClean', got: {v}")
        return v


class JournalctlCleanSSHTask(SSHTask, JournalctlCleanSSHTaskArgs):
    operator: CallablePath = Field(default="airflow_common.JournalctlCleanSSH", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: type) -> type:
        if v is not JournalctlCleanSSH:
            raise ValueError(f"operator must be 'airflow_common.JournalctlCleanSSH', got: {v}")
        return v


# Alias
JournalctlCleanOperator = JournalctlCleanTask
JournalctlCleanSSHOperator = JournalctlCleanSSHTask
