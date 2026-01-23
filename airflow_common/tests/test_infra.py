"""Tests for infrastructure tasks: Systemctl, Reboot, and Lunchy."""

import pytest

from airflow_common.infra.journalctl import (
    clean_journalctl,
)
from airflow_common.infra.launchctl import (
    Lunchy,
    LunchySSH,
    LunchySSHTask,
    LunchySSHTaskArgs,
    LunchyTask,
    LunchyTaskArgs,
    lunchy_command,
)
from airflow_common.infra.reboot import (
    Reboot,
    RebootSSH,
    RebootSSHTask,
    RebootSSHTaskArgs,
    RebootTask,
    RebootTaskArgs,
    reboot_command,
)
from airflow_common.infra.systemctl import (
    Systemctl,
    SystemctlSSH,
    SystemctlSSHTask,
    SystemctlSSHTaskArgs,
    SystemctlTask,
    SystemctlTaskArgs,
    systemctl_command,
)


class TestJournalctlCommands:
    """Test journalctl command generation."""

    def test_clean_journalctl_default(self):
        cmd = clean_journalctl()
        assert cmd == "sudo journalctl --vacuum-time=2d"

    def test_clean_journalctl_no_sudo(self):
        cmd = clean_journalctl(sudo=False)
        assert cmd == "journalctl --vacuum-time=2d"

    def test_clean_journalctl_custom_days(self):
        cmd = clean_journalctl(days=7)
        assert cmd == "sudo journalctl --vacuum-time=7d"

    def test_clean_journalctl_none_days_defaults_to_2(self):
        cmd = clean_journalctl(days=None)
        assert cmd == "sudo journalctl --vacuum-time=2d"


class TestSystemctlCommands:
    """Test systemctl command generation."""

    def test_systemctl_start(self):
        cmd = systemctl_command("airflow-webserver", "start")
        assert cmd == "sudo systemctl start airflow-webserver"

    def test_systemctl_stop(self):
        cmd = systemctl_command("airflow-webserver", "stop")
        assert cmd == "sudo systemctl stop airflow-webserver"

    def test_systemctl_enable(self):
        cmd = systemctl_command("airflow-webserver", "enable")
        assert cmd == "sudo systemctl enable airflow-webserver"

    def test_systemctl_disable(self):
        cmd = systemctl_command("airflow-webserver", "disable")
        assert cmd == "sudo systemctl disable airflow-webserver"

    def test_systemctl_restart(self):
        cmd = systemctl_command("airflow-webserver", "restart")
        assert cmd == "sudo systemctl restart airflow-webserver"

    def test_systemctl_status(self):
        cmd = systemctl_command("airflow-webserver", "status")
        assert cmd == "sudo systemctl status airflow-webserver"

    def test_systemctl_no_sudo(self):
        cmd = systemctl_command("airflow-webserver", "start", sudo=False)
        assert cmd == "systemctl start airflow-webserver"

    def test_systemctl_default_action(self):
        cmd = systemctl_command("airflow-webserver")
        assert cmd == "sudo systemctl restart airflow-webserver"


class TestRebootCommands:
    """Test reboot command generation."""

    def test_reboot_immediate_sudo(self):
        cmd = reboot_command()
        assert cmd == "sudo reboot now"

    def test_reboot_immediate_no_sudo(self):
        cmd = reboot_command(sudo=False)
        assert cmd == "reboot now"

    def test_reboot_delayed_sudo(self):
        cmd = reboot_command(delay_minutes=5)
        assert cmd == "echo 'sudo reboot now' | at now + 5 minutes"

    def test_reboot_delayed_no_sudo(self):
        cmd = reboot_command(sudo=False, delay_minutes=10)
        assert cmd == "echo 'reboot now' | at now + 10 minutes"


class TestLunchyCommands:
    """Test lunchy command generation for macOS."""

    def test_lunchy_start(self):
        cmd = lunchy_command("timkpaine.airflow-webserver", "start")
        assert cmd == "lunchy start timkpaine.airflow-webserver"

    def test_lunchy_stop(self):
        cmd = lunchy_command("timkpaine.airflow-webserver", "stop")
        assert cmd == "lunchy stop timkpaine.airflow-webserver"

    def test_lunchy_restart(self):
        cmd = lunchy_command("timkpaine.airflow-webserver", "restart")
        assert cmd == "lunchy restart timkpaine.airflow-webserver"

    def test_lunchy_status(self):
        cmd = lunchy_command("timkpaine.airflow-webserver", "status")
        assert cmd == "lunchy status timkpaine.airflow-webserver"

    def test_lunchy_list(self):
        cmd = lunchy_command("timkpaine.airflow", "list")
        assert cmd == "lunchy list timkpaine.airflow"

    def test_lunchy_with_sudo(self):
        cmd = lunchy_command("timkpaine.airflow-webserver", "start", sudo=True)
        assert cmd == "sudo lunchy start timkpaine.airflow-webserver"

    def test_lunchy_default_action(self):
        cmd = lunchy_command("timkpaine.airflow-webserver")
        assert cmd == "lunchy restart timkpaine.airflow-webserver"


class TestSystemctlOperators:
    """Test Systemctl operator classes."""

    def test_systemctl_operator_rejects_bash_command(self):
        with pytest.raises(ValueError, match="does not accept 'bash_command'"):
            Systemctl(task_id="test", service="nginx", bash_command="echo test")

    def test_systemctl_ssh_operator_rejects_command(self):
        with pytest.raises(ValueError, match="does not accept 'command'"):
            SystemctlSSH(task_id="test", service="nginx", ssh_conn_id="test", command="echo test")


class TestRebootOperators:
    """Test Reboot operator classes."""

    def test_reboot_operator_rejects_bash_command(self):
        with pytest.raises(ValueError, match="does not accept 'bash_command'"):
            Reboot(task_id="test", bash_command="echo test")

    def test_reboot_ssh_operator_rejects_command(self):
        with pytest.raises(ValueError, match="does not accept 'command'"):
            RebootSSH(task_id="test", ssh_conn_id="test", command="echo test")


class TestLunchyOperators:
    """Test Lunchy operator classes."""

    def test_lunchy_operator_rejects_bash_command(self):
        with pytest.raises(ValueError, match="does not accept 'bash_command'"):
            Lunchy(task_id="test", service="my.service", bash_command="echo test")

    def test_lunchy_ssh_operator_rejects_command(self):
        with pytest.raises(ValueError, match="does not accept 'command'"):
            LunchySSH(task_id="test", service="my.service", ssh_conn_id="test", command="echo test")


class TestSystemctlTaskArgs:
    """Test SystemctlTaskArgs validation."""

    def test_systemctl_task_args_valid(self):
        args = SystemctlTaskArgs(service="nginx", action="start")
        assert args.service == "nginx"
        assert args.action == "start"
        assert args.sudo is True

    def test_systemctl_task_args_no_sudo(self):
        args = SystemctlTaskArgs(service="nginx", action="stop", sudo=False)
        assert args.sudo is False

    def test_systemctl_ssh_task_args_valid(self):
        args = SystemctlSSHTaskArgs(service="nginx", action="enable")
        assert args.service == "nginx"
        assert args.action == "enable"


class TestRebootTaskArgs:
    """Test RebootTaskArgs validation."""

    def test_reboot_task_args_default(self):
        args = RebootTaskArgs()
        assert args.sudo is True
        assert args.delay_minutes is None

    def test_reboot_task_args_with_delay(self):
        args = RebootTaskArgs(delay_minutes=5)
        assert args.delay_minutes == 5

    def test_reboot_ssh_task_args_valid(self):
        args = RebootSSHTaskArgs(sudo=False, delay_minutes=10)
        assert args.sudo is False
        assert args.delay_minutes == 10


class TestLunchyTaskArgs:
    """Test LunchyTaskArgs validation."""

    def test_lunchy_task_args_valid(self):
        args = LunchyTaskArgs(service="timkpaine.airflow-webserver", action="start")
        assert args.service == "timkpaine.airflow-webserver"
        assert args.action == "start"
        assert args.sudo is False  # Default is False for lunchy

    def test_lunchy_task_args_with_sudo(self):
        args = LunchyTaskArgs(service="timkpaine.airflow-webserver", action="stop", sudo=True)
        assert args.sudo is True

    def test_lunchy_ssh_task_args_valid(self):
        args = LunchySSHTaskArgs(service="timkpaine.airflow-webserver", action="restart")
        assert args.service == "timkpaine.airflow-webserver"
        assert args.action == "restart"


class TestSystemctlTasks:
    """Test Systemctl Pydantic tasks."""

    def test_systemctl_task_operator_validation(self):
        task = SystemctlTask(task_id="restart-nginx", service="nginx", action="restart")
        assert task.operator is Systemctl

    def test_systemctl_ssh_task_operator_validation(self):
        task = SystemctlSSHTask(task_id="restart-nginx", service="nginx", action="restart")
        assert task.operator is SystemctlSSH


class TestRebootTasks:
    """Test Reboot Pydantic tasks."""

    def test_reboot_task_operator_validation(self):
        task = RebootTask(task_id="reboot-server")
        assert task.operator is Reboot

    def test_reboot_ssh_task_operator_validation(self):
        task = RebootSSHTask(task_id="reboot-remote")
        assert task.operator is RebootSSH


class TestLunchyTasks:
    """Test Lunchy Pydantic tasks."""

    def test_lunchy_task_operator_validation(self):
        task = LunchyTask(task_id="restart-service", service="timkpaine.airflow-webserver", action="restart")
        assert task.operator is Lunchy

    def test_lunchy_ssh_task_operator_validation(self):
        task = LunchySSHTask(task_id="restart-service", service="timkpaine.airflow-webserver", action="restart")
        assert task.operator is LunchySSH
