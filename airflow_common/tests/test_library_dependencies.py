import pytest
from airflow_pydantic.airflow import DAG, EmptyOperator
from airflow_pydantic.migration import _airflow_3

from airflow_common import InstallLibraryOperator, InstallLibrarySSHOperator

pytestmark = pytest.mark.skipif(_airflow_3() is None, reason="Airflow is not installed")


@pytest.fixture(params=[InstallLibraryOperator, InstallLibrarySSHOperator], ids=["local", "ssh"])
def operator_cls(request):
    return request.param


@pytest.fixture(params=[False, True], ids=["sequential", "parallel"])
def parallel(request):
    return request.param


@pytest.fixture(params=["empty", "pip", "mixed"])
def library_graph(request, operator_cls, parallel):
    libraries = {}
    task_ids = []
    if request.param != "empty":
        libraries["pip"] = [{"name": "package"}]
        task_ids = ["install-package-pip-install"]
    if request.param == "mixed":
        libraries["git"] = [{"name": "repo", "repo": "https://example.invalid/repo.git", "install": False}]
        libraries["conda"] = [{"name": "conda-package"}]
        task_ids = ["install-repo-clone", *task_ids, "install-conda-package-conda-install"]
    kwargs = {"ssh_conn_id": "unused"} if operator_cls is InstallLibrarySSHOperator else {}
    with DAG("library_dependencies", schedule=None) as dag:
        install = operator_cls(task_id="install", parallel=parallel, **libraries, **kwargs)
    leaves = task_ids if parallel and task_ids else task_ids[-1:] or [install.task_id]
    return dag, install, task_ids, leaves


def test_install_graph(library_graph, parallel):
    dag, install, task_ids, leaves = library_graph
    assert set(dag.task_ids) == {install.task_id, *task_ids}
    assert install.roots == [install]
    assert {task.task_id for task in install.leaves} == set(leaves)
    previous = install.task_id
    for task_id in task_ids:
        assert dag.get_task(task_id).upstream_task_ids == {install.task_id if parallel else previous}
        previous = task_id


@pytest.mark.parametrize("wiring", ["shift", "reverse_shift", "setter", "list"])
def test_upstream_dependencies(library_graph, wiring):
    dag, install, _, _ = library_graph
    before = EmptyOperator(task_id="before", dag=dag)
    if wiring == "shift":
        assert before >> install is install
    elif wiring == "reverse_shift":
        assert install << before is before
    elif wiring == "setter":
        install.set_upstream(before)
    else:
        another = EmptyOperator(task_id="another", dag=dag)
        assert [before, another] >> install is install
        assert another.downstream_task_ids == {install.task_id}
    assert before.downstream_task_ids == {install.task_id}
    assert install.upstream_task_ids == ({"before", "another"} if wiring == "list" else {"before"})


@pytest.mark.parametrize("wiring", ["shift", "reverse_shift", "setter", "list"])
def test_downstream_dependencies(library_graph, wiring):
    dag, install, _, leaves = library_graph
    after = EmptyOperator(task_id="after", dag=dag)
    if wiring == "shift":
        assert install >> after is after
    elif wiring == "reverse_shift":
        assert after << install is install
    elif wiring == "setter":
        install.set_downstream(after)
    else:
        another = EmptyOperator(task_id="another", dag=dag)
        assert [after, another] << install is install
        assert another.upstream_task_ids == set(leaves)
    assert after.upstream_task_ids == set(leaves)


def test_chained_dependencies(library_graph):
    dag, install, _, leaves = library_graph
    before = EmptyOperator(task_id="before", dag=dag)
    after = EmptyOperator(task_id="after", dag=dag)
    final = EmptyOperator(task_id="final", dag=dag)
    assert before >> install >> after >> final is final
    assert install.upstream_task_ids == {"before"}
    assert after.upstream_task_ids == set(leaves)
    assert after.downstream_task_ids == {"final"}
    assert final.upstream_task_ids == {"after"}


def test_library_to_library_dependencies(library_graph, operator_cls, parallel):
    dag, install, _, leaves = library_graph
    kwargs = {"ssh_conn_id": "unused"} if operator_cls is InstallLibrarySSHOperator else {}
    other = operator_cls(task_id="other", pip=[{"name": "other-package"}], parallel=parallel, dag=dag, **kwargs)
    assert install >> other is other
    assert other.upstream_task_ids == set(leaves)
