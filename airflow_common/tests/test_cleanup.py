"""Tests for file cleanup and disk usage check tasks."""

import os
import subprocess
import time

import pytest
from airflow_config import load_config

from airflow_common.infra.cleanup import FileCleanup, FileCleanupSSH, FileCleanupSSHTask, FileCleanupTask, file_cleanup_command
from airflow_common.infra.disk import DiskUsageCheck, DiskUsageCheckSSH, DiskUsageCheckSSHTask, DiskUsageCheckTask, disk_usage_check_command


def _age(path, days):
    stamp = time.time() - days * 86400
    os.utime(path, (stamp, stamp))


class TestFileCleanupCommand:
    def test_default(self):
        assert file_cleanup_command(["/var/log/app"]) == (
            "find /var/log/app -type f -mtime +30 -delete && find /var/log/app -mindepth 1 -type d -empty -delete"
        )

    def test_pattern_sudo_and_quoting(self):
        cmd = file_cleanup_command(["/var/tmp/my app"], days=7, pattern="*.tmp", remove_empty_dirs=False, sudo=True)
        assert cmd == "sudo find '/var/tmp/my app' -type f -name '*.tmp' -mtime +7 -delete"

    def test_multiple_paths(self):
        cmd = file_cleanup_command(["/a", "/b"], days=2, remove_empty_dirs=False)
        assert cmd == "find /a -type f -mtime +2 -delete && find /b -type f -mtime +2 -delete"

    @pytest.mark.parametrize("kwargs", [{"paths": []}, {"paths": ["/a"], "days": 0}])
    def test_invalid(self, kwargs):
        with pytest.raises(ValueError):
            file_cleanup_command(**kwargs)

    def test_deletes_only_old_files_and_empty_directories(self, tmp_path):
        old = tmp_path / "dag" / "old.log"
        new = tmp_path / "dag" / "new.log"
        stale_dir = tmp_path / "empty"
        old.parent.mkdir()
        stale_dir.mkdir()
        old.write_text("old")
        new.write_text("new")
        _age(old, 40)

        subprocess.run(["bash", "-c", file_cleanup_command([str(tmp_path)], days=30)], check=True)

        assert not old.exists()
        assert new.exists()
        assert not stale_dir.exists()
        assert tmp_path.exists()

    def test_missing_path_fails(self, tmp_path):
        result = subprocess.run(["bash", "-c", file_cleanup_command([str(tmp_path / "missing")])], check=False, capture_output=True)
        assert result.returncode != 0


class TestDiskUsageCheckCommand:
    def test_default_checks_root(self):
        assert disk_usage_check_command().startswith("df -P / | awk ")

    def test_invalid_threshold(self):
        with pytest.raises(ValueError):
            disk_usage_check_command(threshold=0)

    def test_passes_under_threshold_and_fails_over_it(self, tmp_path):
        ok = subprocess.run(["bash", "-c", disk_usage_check_command([str(tmp_path)], threshold=100)], check=False, capture_output=True, text=True)
        over = subprocess.run(["bash", "-c", disk_usage_check_command([str(tmp_path)], threshold=1)], check=False, capture_output=True, text=True)

        assert ok.returncode == 0 and ok.stdout.strip().endswith("ok")
        # Any filesystem in use is more than 1% full, unless it is empty.
        assert over.returncode == 1 and over.stdout.strip().endswith("over")


class TestTaskModels:
    def test_task_args_validate(self):
        with pytest.raises(ValueError):
            FileCleanupTask(task_id="clean", paths=[])
        with pytest.raises(ValueError):
            DiskUsageCheckTask(task_id="check", threshold=101)
        assert FileCleanupSSHTask(task_id="clean", ssh_conn_id="worker", paths=["/tmp"]).days == 30
        assert DiskUsageCheckSSHTask(task_id="check", ssh_conn_id="worker").threshold == 85

    def test_render_from_config(self):
        config = load_config(config_name="config")
        clean = config.dags["clean-files"].render()
        check = config.dags["check-disk"].render()

        assert 'FileCleanup(paths=["/var/log/app", "/var/tmp/app"], days=30, task_id="clean", dag=dag)' in clean
        assert 'FileCleanupSSH(ssh_conn_id="worker", paths=["/var/tmp/app"], days=7, pattern="*.tmp", task_id="clean-remote", dag=dag)' in clean
        assert 'DiskUsageCheck(paths=["/", "/var"], threshold=85, task_id="check", dag=dag)' in check
        assert 'DiskUsageCheckSSH(ssh_conn_id="worker", threshold=90, task_id="check-remote", dag=dag)' in check


class TestOperators:
    def test_operators_reject_raw_commands(self):
        with pytest.raises(ValueError, match="does not accept 'bash_command'"):
            FileCleanup(task_id="clean", paths=["/tmp"], bash_command="echo test")
        with pytest.raises(ValueError, match="does not accept 'command'"):
            FileCleanupSSH(task_id="clean", paths=["/tmp"], ssh_conn_id="worker", command="echo test")
        with pytest.raises(ValueError, match="does not accept 'bash_command'"):
            DiskUsageCheck(task_id="check", bash_command="echo test")
        with pytest.raises(ValueError, match="does not accept 'command'"):
            DiskUsageCheckSSH(task_id="check", ssh_conn_id="worker", command="echo test")

    def test_operators_build_their_commands(self):
        pytest.importorskip("airflow")
        assert FileCleanup(task_id="clean", paths=["/tmp/x"], days=3).bash_command == file_cleanup_command(["/tmp/x"], days=3)
        assert FileCleanupSSH(task_id="clean", paths=["/tmp/x"], ssh_conn_id="worker").command == file_cleanup_command(["/tmp/x"])
        assert DiskUsageCheck(task_id="check", threshold=90).bash_command == disk_usage_check_command(threshold=90)
        assert DiskUsageCheckSSH(task_id="check", paths=["/var"], ssh_conn_id="worker").command == disk_usage_check_command(["/var"])

    def test_task_models_pin_their_operators(self):
        assert FileCleanupTask(task_id="clean", paths=["/tmp"]).operator is FileCleanup
        assert FileCleanupSSHTask(task_id="clean", paths=["/tmp"]).operator is FileCleanupSSH
        assert DiskUsageCheckTask(task_id="check").operator is DiskUsageCheck
        assert DiskUsageCheckSSHTask(task_id="check").operator is DiskUsageCheckSSH
        with pytest.raises(ValueError, match="operator must be"):
            FileCleanupTask(task_id="clean", paths=["/tmp"], operator="airflow_common.DiskUsageCheck")
        with pytest.raises(ValueError, match="operator must be"):
            FileCleanupSSHTask(task_id="clean", paths=["/tmp"], operator="airflow_common.DiskUsageCheck")
        with pytest.raises(ValueError, match="operator must be"):
            DiskUsageCheckTask(task_id="check", operator="airflow_common.FileCleanup")
        with pytest.raises(ValueError, match="operator must be"):
            DiskUsageCheckSSHTask(task_id="check", operator="airflow_common.FileCleanup")
