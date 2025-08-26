from unittest.mock import MagicMock, call, patch

import pytest
from airflow_pydantic import fail, pass_

from airflow_common import all_success_any_failure, if_booted_do


class TestHelpers:
    @pytest.mark.parametrize("make_list", [True, False])
    def test_if_booted_do(self, make_list):
        with (
            patch("airflow_common.airflow.topology.PythonOperator") as mock_python_operator,
            patch("airflow_common.airflow.topology.ping") as mock_ping,
        ):
            if make_list:
                task = if_booted_do(task_id="task", host="host", task=[MagicMock()])
            else:
                task = if_booted_do(task_id="task", host="host", task=MagicMock())
            mock_ping.assert_called_once_with("host")
            mock_python_operator.assert_called_once_with(
                task_id="task-check-if-booted-host",
                python_callable=mock_ping.return_value,
            )
            if make_list:
                mock_python_operator.return_value.__rshift__.assert_called_once_with(task[0])
            else:
                mock_python_operator.return_value.__rshift__.assert_called_once_with(task)

    def test_all_success_any_failure(self):
        with patch("airflow_common.airflow.topology.PythonOperator") as mock_python_operator:
            task = MagicMock()
            dag = MagicMock()

            any_ssh_failure, all_ssh_success = all_success_any_failure(
                task_id="task",
                tasks=[task],
                dag=dag,
                queue="blerg",
            )

            mock_python_operator.assert_has_calls(
                [
                    call(task_id="task-any-failure", python_callable=fail, queue="blerg", trigger_rule="one_failed", dag=dag),
                    call(task_id="task-all-success", python_callable=pass_, queue="blerg", trigger_rule="none_failed", dag=dag),
                ]
            )
            task.__rshift__.assert_has_calls(
                [
                    call(any_ssh_failure),
                    call(all_ssh_success),
                ]
            )
