from typing import List, Optional, Type

from airflow_pydantic import BashTask, BashTaskArgs, ImportPath, SSHTask, SSHTaskArgs
from airflow_pydantic.airflow import PythonOperator
from pydantic import Field, field_validator

from .model import CondaLibrary, GitRepo, LibraryList, PipLibrary

__all__ = (
    "LibraryOperatorBase",
    "InstallLibraryOperator",
    "InstallLibrarySSHOperator",
    "LibraryListTaskArgs",
    "LibraryListSSHTaskArgs",
    "LibraryListTask",
    "LibraryListSSHTask",
)


class LibraryOperatorBase(PythonOperator):
    _first_command: "PythonOperator"
    _last_command: "PythonOperator"

    def __init__(
        self,
        task_id: str,
        pip: List[PipLibrary],
        conda: List[CondaLibrary],
        git: List[GitRepo],
        operator,
        operator_command_arg,
        parallel: Optional[bool] = False,
        command_prefix: Optional[str] = "",
        **kwargs,
    ):
        self.pip = pip
        self.conda = conda
        self.git = git
        self.operator = operator
        self.parallel = parallel
        if command_prefix:
            self.command_prefix = f"{command_prefix}\n"
        else:
            self.command_prefix = ""

        # Print info, run each git library, run each pip library
        info = []
        for lib in self.git:
            info.append(f"Git library: {lib}")
        for lib in self.pip:
            info.append(f"Pip library: {lib}")
        for lib in self.conda:
            info.append(f"Conda library: {lib}")

        # Initialize self
        super().__init__(
            task_id=f"{task_id}-info",
            python_callable=lambda: print("\n".join(info)),
            dag=kwargs.get("dag", None),
        )

        # Setup deps
        last_command = self
        for git_repo in self.git:
            git_repo_clone_op = self.operator(
                task_id=f"{task_id}-{git_repo.name}-clone",
                **{operator_command_arg: f"{self.command_prefix}{git_repo.clone()}"},
                **kwargs,
            )
            # NOTE: overloading shift so use parent's
            PythonOperator.set_downstream(last_command, git_repo_clone_op)
            last_command = self if self.parallel else git_repo_clone_op

        for pip_lib in self.pip:
            pip_lib_install_op = self.operator(
                task_id=f"{task_id}-{pip_lib.name}-pip-install",
                **{operator_command_arg: f"{self.command_prefix}{pip_lib.install()}"},
                **kwargs,
            )
            # NOTE: overloading shift so use parent's
            PythonOperator.set_downstream(last_command, pip_lib_install_op)
            last_command = self if self.parallel else pip_lib_install_op

        for conda_lib in self.conda:
            conda_lib_install_op = self.operator(
                task_id=f"{task_id}-{conda_lib.name}-conda-install",
                **{operator_command_arg: f"{self.command_prefix}{conda_lib.install()}"},
                **kwargs,
            )
            # NOTE: overloading shift so use parent's
            PythonOperator.set_downstream(last_command, conda_lib_install_op)
            last_command = self if self.parallel else conda_lib_install_op

        # Overload sequence
        self._first_command = self
        self._last_command = last_command

    def __lshift__(self, other):
        """<<"""
        self._first_command << other
        return self

    def __rshift__(self, other):
        """>>"""
        self._last_command >> other
        return self

    def set_upstream(self, other):
        self._first_command.set_upstream(other)
        return self

    def set_downstream(self, other):
        self._last_command.set_downstream(other)


class InstallLibraryOperator(LibraryOperatorBase):
    _original = "airflow_common.library.task.InstallLibraryOperator"

    def __init__(
        self,
        task_id: str,
        pip: Optional[List[PipLibrary]] = None,
        conda: Optional[List[CondaLibrary]] = None,
        git: Optional[List[GitRepo]] = None,
        parallel: Optional[bool] = False,
        command_prefix: Optional[str] = "",
        **kwargs,
    ):
        from airflow.providers.standard.operators.bash import BashOperator

        obj = LibraryListTaskArgs.model_validate(
            {"pip": pip or [], "conda": conda or [], "git": git or [], "parallel": parallel, "command_prefix": command_prefix}
        )

        super().__init__(
            task_id=task_id,
            pip=obj.pip,
            conda=obj.conda,
            git=obj.git,
            parallel=obj.parallel,
            command_prefix=obj.command_prefix,
            operator=BashOperator,
            operator_command_arg="bash_command",
            **kwargs,
        )


class InstallLibrarySSHOperator(LibraryOperatorBase):
    _original = "airflow_common.library.task.InstallLibrarySSHOperator"

    def __init__(
        self,
        task_id: str,
        pip: Optional[List[PipLibrary]] = None,
        conda: Optional[List[CondaLibrary]] = None,
        git: Optional[List[GitRepo]] = None,
        parallel: Optional[bool] = False,
        command_prefix: Optional[str] = "",
        **kwargs,
    ):
        from airflow.providers.ssh.operators.ssh import SSHOperator

        obj = LibraryListSSHTaskArgs.model_validate(
            {"pip": pip or [], "conda": conda or [], "git": git or [], "parallel": parallel, "command_prefix": command_prefix}
        )
        super().__init__(
            task_id=task_id,
            pip=obj.pip,
            conda=obj.conda,
            git=obj.git,
            parallel=obj.parallel,
            command_prefix=obj.command_prefix,
            operator=SSHOperator,
            operator_command_arg="command",
            **kwargs,
        )


class LibraryListTaskArgs(BashTaskArgs, LibraryList): ...


class LibraryListSSHTaskArgs(SSHTaskArgs, LibraryList): ...


class LibraryListTask(BashTask, LibraryListTaskArgs):
    operator: ImportPath = Field(default="airflow_common.InstallLibraryOperator", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Type) -> Type:
        if not isinstance(v, Type) and issubclass(v, InstallLibraryOperator):
            raise ValueError(f"operator must be 'airflow_common.InstallLibraryOperator', got: {v}")
        return v


class LibraryListSSHTask(SSHTask, LibraryListTaskArgs):
    operator: ImportPath = Field(default="airflow_common.InstallLibrarySSHOperator", validate_default=True)

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Type) -> Type:
        if not isinstance(v, Type) and issubclass(v, InstallLibrarySSHOperator):
            raise ValueError(f"operator must be 'airflow_common.InstallLibrarySSHOperator', got: {v}")
        return v
