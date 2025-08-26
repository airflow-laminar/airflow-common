from typing import List, Literal

from airflow_pydantic import BaseModel, BashCommands
from pydantic import Field

__all__ = (
    "clone_repo",
    "GitRepo",
    "PipLibrary",
    "LibraryList",
    "Library",
    "Tool",
)


Tool = Literal["pip", "uv"]


def clone_repo(
    name: str,
    repo: str,
    branch: str = "main",
    *,
    clean: bool = False,
    install: bool = True,
    install_deps: bool = False,
    editable: bool = True,
    tool: Tool = "pip",
    dir: str = "",
):
    cmds = [
        f"[[ -d {name} ]] || git clone {repo}",
        f"pushd {name}",
        "git stash",
    ]
    if clean:
        cmds.append("git clean -fdx")
    cmds.extend(
        [
            "git fetch --all --force",
            f"git checkout {branch}",
            f"git reset origin/{branch} --hard",
        ]
    )
    if dir:
        cmds.insert(0, f"cd {dir}")
        cmds.insert(0, f"mkdir -p {dir}")
    if install:
        tool = "uv pip" if tool == "uv" else "pip"
        install_deps_flag = "" if install_deps else "--no-deps "
        editable_flag = "-e " if editable else ""
        cmd = f"{tool} install {install_deps_flag}{editable_flag}."
        cmds.append(f"{cmd}")
    return BashCommands(commands=cmds)._serialize()


class GitRepo(BaseModel):
    name: str
    repo: str
    branch: str = "main"

    clean: bool = False
    install: bool = True
    install_deps: bool = False
    editable: bool = True
    tool: Tool = "pip"
    dir: str = ""

    def clone(self):
        return clone_repo(
            name=self.name,
            repo=self.repo,
            branch=self.branch,
            clean=self.clean,
            install=self.install,
            install_deps=self.install_deps,
            editable=self.editable,
            tool=self.tool,
            dir=self.dir,
        )


class PipLibrary(BaseModel):
    name: str

    version_constraint: str = ""
    install_deps: bool = False
    reinstall: bool = False
    tool: Tool = "pip"
    dir: str = ""

    def install(self):
        tool = "uv pip" if self.tool == "uv" else "pip"
        install_deps_flag = "" if self.install_deps else "--no-deps "
        install_dir_flag = "" if not self.dir else f"--target {self.dir} "
        reinstall_flag = "--force-reinstall " if self.reinstall else ""
        return BashCommands(
            commands=[f'{tool} install {install_deps_flag}{install_dir_flag}{reinstall_flag}"{self.name}{self.version_constraint}"']
        )._serialize()


class LibraryList(BaseModel):
    pip: List[PipLibrary] = Field(default_factory=list)
    git: List[GitRepo] = Field(default_factory=list)


# Alias
Library = LibraryList
