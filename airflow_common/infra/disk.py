from shlex import quote

from airflow_pydantic import BashTask, BashTaskArgs, CallablePath, SSHTask, SSHTaskArgs
from airflow_pydantic.airflow import BashOperator, SSHOperator
from pydantic import Field, field_validator

__all__ = (
    "DiskUsageCheck",
    "DiskUsageCheckOperator",
    "DiskUsageCheckOperatorArgs",
    "DiskUsageCheckSSH",
    "DiskUsageCheckSSHOperator",
    "DiskUsageCheckSSHOperatorArgs",
    "DiskUsageCheckSSHTask",
    "DiskUsageCheckSSHTaskArgs",
    "DiskUsageCheckTask",
    "DiskUsageCheckTaskArgs",
    "disk_usage_check_command",
)


def disk_usage_check_command(paths: list[str] | None = None, threshold: int = 85) -> str:
    """Generate a command that prints the usage of the filesystems holding ``paths`` and fails if any is above ``threshold`` percent."""
    paths = paths or ["/"]
    if not 0 < threshold <= 100:
        raise ValueError("threshold must be between 1 and 100.")
    targets = " ".join(quote(path) for path in paths)
    script = (
        f'NR > 1 {{ used = $5; sub("%", "", used); status = (used + 0 > {threshold}) ? "over" : "ok"; '
        f'print $6, $5, status; if (status == "over") failed = 1 }} END {{ exit failed }}'
    )
    return f"df -P {targets} | awk {quote(script)}"


class DiskUsageCheck(BashOperator):
    _original = "airflow_common.infra.disk.DiskUsageCheck"

    def __init__(self, paths: list[str] | None = None, threshold: int = 85, **kwargs):
        if "bash_command" in kwargs:
            raise ValueError("DiskUsageCheck does not accept 'bash_command' as an argument.")
        super().__init__(bash_command=disk_usage_check_command(paths=paths, threshold=threshold), **kwargs)


class DiskUsageCheckSSH(SSHOperator):
    _original = "airflow_common.infra.disk.DiskUsageCheckSSH"

    def __init__(self, paths: list[str] | None = None, threshold: int = 85, **kwargs):
        if "command" in kwargs:
            raise ValueError("DiskUsageCheckSSH does not accept 'command' as an argument.")
        super().__init__(command=disk_usage_check_command(paths=paths, threshold=threshold), **kwargs)


class DiskUsageCheckTaskArgs(BashTaskArgs):
    paths: list[str] | None = Field(default=None, description="Paths whose filesystems to check; defaults to /.")
    threshold: int = Field(default=85, gt=0, le=100, description="Fail when a filesystem is more than this percent full.")


class DiskUsageCheckSSHTaskArgs(SSHTaskArgs):
    paths: list[str] | None = Field(default=None, description="Paths whose filesystems to check; defaults to /.")
    threshold: int = Field(default=85, gt=0, le=100, description="Fail when a filesystem is more than this percent full.")


# Alias
DiskUsageCheckOperatorArgs = DiskUsageCheckTaskArgs
DiskUsageCheckSSHOperatorArgs = DiskUsageCheckSSHTaskArgs


class DiskUsageCheckTask(BashTask, DiskUsageCheckTaskArgs):
    operator: CallablePath = Field(default="airflow_common.DiskUsageCheck", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: type) -> type:
        if v is not DiskUsageCheck:
            raise ValueError(f"operator must be 'airflow_common.DiskUsageCheck', got: {v}")
        return v


class DiskUsageCheckSSHTask(SSHTask, DiskUsageCheckSSHTaskArgs):
    operator: CallablePath = Field(default="airflow_common.DiskUsageCheckSSH", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: type) -> type:
        if v is not DiskUsageCheckSSH:
            raise ValueError(f"operator must be 'airflow_common.DiskUsageCheckSSH', got: {v}")
        return v


# Alias
DiskUsageCheckOperator = DiskUsageCheckTask
DiskUsageCheckSSHOperator = DiskUsageCheckSSHTask
