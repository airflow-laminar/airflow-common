from shlex import quote
from typing import TYPE_CHECKING

from airflow_pydantic import BashTask, BashTaskArgs, ImportPath, SSHTask, SSHTaskArgs
from pydantic import Field, field_validator

if TYPE_CHECKING:
    from airflow.providers.ssh.operators.ssh import SSHOperator
    from airflow.providers.standard.operators.bash import BashOperator
else:
    from airflow_pydantic.airflow import BashOperator, SSHOperator

__all__ = (
    "FileCleanup",
    "FileCleanupOperator",
    "FileCleanupOperatorArgs",
    "FileCleanupSSH",
    "FileCleanupSSHOperator",
    "FileCleanupSSHOperatorArgs",
    "FileCleanupSSHTask",
    "FileCleanupSSHTaskArgs",
    "FileCleanupTask",
    "FileCleanupTaskArgs",
    "file_cleanup_command",
)


def file_cleanup_command(
    paths: list[str],
    days: int = 30,
    pattern: str | None = None,
    remove_empty_dirs: bool = True,
    sudo: bool | None = False,
    missing_ok: bool = False,
) -> str:
    """Generate a command that deletes files under each path last modified more than ``days`` days ago.

    ``pattern`` limits deletion to file names matching a shell glob. Empty directories left behind are removed,
    except the paths themselves. A path that does not exist fails the command unless ``missing_ok`` is set, which
    skips it instead, for paths that exist on only some hosts.
    """
    if not paths:
        raise ValueError("file_cleanup_command requires at least one path.")
    if days < 1:
        raise ValueError("days must be at least 1.")
    find = "sudo find" if sudo else "find"
    name = f" -name {quote(pattern)}" if pattern else ""
    commands = []
    for path in paths:
        steps = [f"{find} {quote(path)} -type f{name} -mtime +{days} -delete"]
        if remove_empty_dirs:
            steps.append(f"{find} {quote(path)} -mindepth 1 -type d -empty -delete")
        step = " && ".join(steps)
        commands.append(f"{{ [ ! -e {quote(path)} ] || {{ {step}; }}; }}" if missing_ok else step)
    return " && ".join(commands)


class FileCleanup(BashOperator):
    _original = "airflow_common.infra.cleanup.FileCleanup"

    def __init__(
        self,
        paths: list[str],
        days: int = 30,
        pattern: str | None = None,
        remove_empty_dirs: bool = True,
        sudo: bool | None = False,
        missing_ok: bool = False,
        **kwargs,
    ):
        if "bash_command" in kwargs:
            raise ValueError("FileCleanup does not accept 'bash_command' as an argument.")
        super().__init__(
            bash_command=file_cleanup_command(
                paths=paths, days=days, pattern=pattern, remove_empty_dirs=remove_empty_dirs, sudo=sudo, missing_ok=missing_ok
            ),
            **kwargs,
        )


class FileCleanupSSH(SSHOperator):
    _original = "airflow_common.infra.cleanup.FileCleanupSSH"

    def __init__(
        self,
        paths: list[str],
        days: int = 30,
        pattern: str | None = None,
        remove_empty_dirs: bool = True,
        sudo: bool | None = False,
        missing_ok: bool = False,
        **kwargs,
    ):
        if "command" in kwargs:
            raise ValueError("FileCleanupSSH does not accept 'command' as an argument.")
        super().__init__(
            command=file_cleanup_command(
                paths=paths, days=days, pattern=pattern, remove_empty_dirs=remove_empty_dirs, sudo=sudo, missing_ok=missing_ok
            ),
            **kwargs,
        )


class FileCleanupTaskArgs(BashTaskArgs):
    paths: list[str] = Field(..., min_length=1, description="Directories to clean.")
    days: int = Field(default=30, ge=1, description="Delete files last modified more than this many days ago.")
    pattern: str | None = Field(default=None, description="Only delete files whose names match this shell glob.")
    remove_empty_dirs: bool = Field(default=True)
    sudo: bool | None = Field(default=False)
    missing_ok: bool = Field(default=False, description="Skip paths that do not exist instead of failing.")


class FileCleanupSSHTaskArgs(SSHTaskArgs):
    paths: list[str] = Field(..., min_length=1, description="Directories to clean.")
    days: int = Field(default=30, ge=1, description="Delete files last modified more than this many days ago.")
    pattern: str | None = Field(default=None, description="Only delete files whose names match this shell glob.")
    remove_empty_dirs: bool = Field(default=True)
    sudo: bool | None = Field(default=False)
    missing_ok: bool = Field(default=False, description="Skip paths that do not exist instead of failing.")


# Alias
FileCleanupOperatorArgs = FileCleanupTaskArgs
FileCleanupSSHOperatorArgs = FileCleanupSSHTaskArgs


class FileCleanupTask(BashTask, FileCleanupTaskArgs):
    operator: ImportPath = Field(default="airflow_common.FileCleanup", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: type) -> type:
        if v is not FileCleanup:
            raise ValueError(f"operator must be 'airflow_common.FileCleanup', got: {v}")
        return v


class FileCleanupSSHTask(SSHTask, FileCleanupSSHTaskArgs):
    operator: ImportPath = Field(default="airflow_common.FileCleanupSSH", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: type) -> type:
        if v is not FileCleanupSSH:
            raise ValueError(f"operator must be 'airflow_common.FileCleanupSSH', got: {v}")
        return v


# Alias
FileCleanupOperator = FileCleanupTask
FileCleanupSSHOperator = FileCleanupSSHTask
