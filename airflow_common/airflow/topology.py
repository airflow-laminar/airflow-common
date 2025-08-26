from typing import TYPE_CHECKING, List, Optional

from airflow_pydantic import fail, pass_, ping
from airflow_pydantic.airflow import PythonOperator

if TYPE_CHECKING:
    from airflow.models.baseoperator import BaseOperator
    from airflow.models.dag import DAG

__all__ = ("all_success_any_failure", "if_booted_do")


def all_success_any_failure(
    *,
    task_id: str,
    tasks: List["BaseOperator"],
    dag: "DAG",
    queue: Optional[str] = None,
):
    any_ssh_failure = PythonOperator(
        task_id=f"{task_id}-any-failure",
        python_callable=fail,
        queue=queue,
        trigger_rule="one_failed",
        dag=dag,
    )
    all_ssh_success = PythonOperator(
        task_id=f"{task_id}-all-success",
        python_callable=pass_,
        queue=queue,
        trigger_rule="none_failed",
        dag=dag,
    )

    for task in tasks:
        task >> any_ssh_failure
        task >> all_ssh_success

    return any_ssh_failure, all_ssh_success


def if_booted_do(task_id: str, host: str, task: "BaseOperator", **check_operators_kwargs) -> "BaseOperator":
    check_if_booted = PythonOperator(
        task_id=f"{task_id}-check-if-booted-{host}",
        python_callable=ping(host),
        **check_operators_kwargs,
    )

    if isinstance(task, list):
        for task_instance in task:
            check_if_booted >> task_instance
    else:
        check_if_booted >> task
    return task
