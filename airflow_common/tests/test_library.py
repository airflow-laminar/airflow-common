from airflow_common import CondaLibrary, GitRepo, PipLibrary, clone_repo


class TestLibrary:
    def test_pip(self):
        p = PipLibrary(name="tmp", version_constraint="<5", install_deps=False, tool="uv")
        assert p.install() == "bash -lc 'set -ex\nuv pip install --no-deps \"tmp<5\"'"
        p = PipLibrary(name="tmp", version_constraint="", install_deps=True, tool="pip", dir="/tmp")
        assert p.install() == "bash -lc 'set -ex\npip install --target /tmp \"tmp\"'"
        p = PipLibrary(name="tmp", version_constraint=">=3.2", install_deps=True, tool="pip", dir="/tmp")
        assert p.install() == "bash -lc 'set -ex\npip install --target /tmp \"tmp>=3.2\"'"
        p = PipLibrary(name="tmp", version_constraint=">=3.2", install_deps=True, reinstall=True, tool="pip", dir="/tmp")
        assert p.install() == "bash -lc 'set -ex\npip install --target /tmp --force-reinstall \"tmp>=3.2\"'"

    def test_conda(self):
        c = CondaLibrary(name="tmp", version_constraint="<5", install_deps=False, tool="conda")
        assert c.install() == "bash -lc 'set -ex\nconda install -y --no-deps \"tmp<5\"'"
        c = CondaLibrary(name="tmp", version_constraint="", install_deps=True, tool="conda", prefix="/tmp")
        assert c.install() == "bash -lc 'set -ex\nconda install -y --prefix /tmp \"tmp\"'"
        c = CondaLibrary(name="tmp", version_constraint=">=3.2", install_deps=True, tool="mamba", env="tmp")
        assert c.install() == "bash -lc 'set -ex\nmamba install -y --name tmp \"tmp>=3.2\"'"
        c = CondaLibrary(name="tmp", version_constraint=">=3.2", install_deps=True, reinstall=True, tool="micromamba", prefix="/tmp")
        assert c.install() == "bash -lc 'set -ex\nmicromamba install -y --prefix /tmp --force-reinstall \"tmp>=3.2\"'"

    def test_git(self):
        g = GitRepo(name="tmp", repo="tmp", branch="main", clean=True, install=True, install_deps=False, tool="uv")
        assert (
            g.clone()
            == "bash -lc 'set -ex\n[[ -d tmp ]] || git clone tmp\npushd tmp\ngit stash\ngit clean -fdx\ngit fetch --all --force\ngit checkout main\ngit reset origin/main --hard\nuv pip install --no-deps -e .'"
        )
        g = GitRepo(name="tmp", repo="tmp", branch="main", install=True, install_deps=True, tool="pip", dir="/tmp")
        assert (
            g.clone()
            == "bash -lc 'set -ex\nmkdir -p /tmp\ncd /tmp\n[[ -d tmp ]] || git clone tmp\npushd tmp\ngit stash\ngit fetch --all --force\ngit checkout main\ngit reset origin/main --hard\npip install -e .'"
        )
        g = GitRepo(name="tmp", repo="tmp", branch="main", install=True, install_deps=True, tool="pip", dir="/tmp", editable=False)
        assert (
            g.clone()
            == "bash -lc 'set -ex\nmkdir -p /tmp\ncd /tmp\n[[ -d tmp ]] || git clone tmp\npushd tmp\ngit stash\ngit fetch --all --force\ngit checkout main\ngit reset origin/main --hard\npip install .'"
        )

        assert (
            clone_repo(name="tmp", repo="tmp", branch="main", install=False, install_deps=True, tool="uv")
            == "bash -lc 'set -ex\n[[ -d tmp ]] || git clone tmp\npushd tmp\ngit stash\ngit fetch --all --force\ngit checkout main\ngit reset origin/main --hard'"
        )
