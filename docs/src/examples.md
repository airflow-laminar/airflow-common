# Examples

This page provides comprehensive examples of using `airflow-common` for various use cases.

## Common Operators

### Skip, Fail, and Pass Operators

Use these convenience operators for common workflow patterns:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow_common import Skip, Fail, Pass

def check_condition(**kwargs):
    # Your condition logic
    return True

with DAG(
    dag_id="conditional-workflow",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    check = PythonOperator(
        task_id="check-condition",
        python_callable=check_condition,
    )

    # Success path
    success_path = Pass(task_id="success-path", trigger_rule="none_failed")

    # Failure path
    failure_path = Fail(task_id="failure-path", trigger_rule="one_failed")

    # Skip path (for optional tasks)
    skip_path = Skip(task_id="skip-path")

    check >> [success_path, failure_path]
```

## Topology Helpers

### All Success / Any Failure Pattern

Aggregate results from multiple parallel tasks:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator
from airflow_common import all_success_any_failure

with DAG(
    dag_id="parallel-aggregation",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Create multiple parallel tasks
    parallel_tasks = [
        BashOperator(task_id=f"process-{i}", bash_command=f"echo 'Processing {i}'")
        for i in range(5)
    ]

    # Aggregate success/failure
    any_failure, all_success = all_success_any_failure(
        task_id="aggregate",
        tasks=parallel_tasks,
        dag=dag,
    )

    # Continue workflow based on aggregation
    next_step = BashOperator(task_id="next-step", bash_command="echo 'All done!'")
    all_success >> next_step
```

### Conditional Execution Based on Host Availability

Execute tasks only if a host is reachable:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator
from airflow_common import if_booted_do

with DAG(
    dag_id="host-conditional",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Only run if host is available
    deploy_task = BashOperator(
        task_id="deploy",
        bash_command="deploy.sh",
    )

    if_booted_do(
        task_id="deploy-to-server",
        host="server.example.com",
        task=deploy_task,
        dag=dag,
    )
```

## Library Management

### Installing Pip Libraries

Define and install pip packages:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import PipLibrary, InstallLibraryOperator

with DAG(
    dag_id="install-pip-libraries",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Define libraries
    libraries = [
        PipLibrary(name="pandas", version_constraint=">=2.0"),
        PipLibrary(name="numpy"),
        PipLibrary(name="scikit-learn", reinstall=True),
    ]

    install_task = InstallLibraryOperator(
        task_id="install-libs",
        pip=libraries,
        conda=[],
        git=[],
    )
```

### Installing from Git Repositories

Clone and install from git repositories:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import GitRepo, InstallLibraryOperator

with DAG(
    dag_id="install-git-repos",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Define git repositories
    repos = [
        GitRepo(
            name="my-package",
            repo="https://github.com/my-org/my-package.git",
            branch="main",
            install=True,
            editable=True,
        ),
        GitRepo(
            name="another-package",
            repo="https://github.com/my-org/another-package.git",
            branch="develop",
            clean=True,  # Clean before checkout
            install=True,
            install_deps=True,
        ),
    ]

    install_task = InstallLibraryOperator(
        task_id="install-repos",
        pip=[],
        conda=[],
        git=repos,
    )
```

### Installing Conda Libraries

Define and install conda packages:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import CondaLibrary, InstallLibraryOperator

with DAG(
    dag_id="install-conda-libraries",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Define conda libraries
    libraries = [
        CondaLibrary(
            name="tensorflow",
            env="ml-env",  # Install in specific environment
        ),
        CondaLibrary(
            name="pytorch",
            tool="mamba",  # Use mamba for faster installs
        ),
    ]

    install_task = InstallLibraryOperator(
        task_id="install-conda-libs",
        pip=[],
        conda=libraries,
        git=[],
    )
```

### Combined Library List

Install multiple types of libraries together:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import (
    PipLibrary,
    CondaLibrary,
    GitRepo,
    LibraryList,
    InstallLibraryOperator,
)

with DAG(
    dag_id="install-all-libraries",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Define all libraries
    library_list = LibraryList(
        pip=[
            PipLibrary(name="requests"),
            PipLibrary(name="pydantic", version_constraint=">=2"),
        ],
        conda=[
            CondaLibrary(name="numpy"),
        ],
        git=[
            GitRepo(
                name="my-lib",
                repo="https://github.com/my-org/my-lib.git",
                branch="main",
                install=True,
            ),
        ],
        parallel=True,  # Install in parallel when possible
    )

    install_task = InstallLibraryOperator(
        task_id="install-all",
        pip=library_list.pip,
        conda=library_list.conda,
        git=library_list.git,
        parallel=library_list.parallel,
    )
```

### Remote Library Installation via SSH

Install libraries on remote machines:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import PipLibrary, GitRepo, InstallLibrarySSHOperator

with DAG(
    dag_id="install-remote-libraries",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    install_task = InstallLibrarySSHOperator(
        task_id="install-on-remote",
        pip=[
            PipLibrary(name="pandas"),
            PipLibrary(name="numpy"),
        ],
        conda=[],
        git=[
            GitRepo(
                name="my-app",
                repo="https://github.com/my-org/my-app.git",
                branch="main",
                install=True,
            ),
        ],
        ssh_conn_id="my-remote-server",
        command_prefix="source /opt/venv/bin/activate",
    )
```

## Infrastructure Tasks

### Journalctl Cleanup

Clean systemd journal logs to free disk space:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import JournalctlClean, JournalctlCleanSSH

with DAG(
    dag_id="infrastructure-cleanup",
    schedule=timedelta(days=7),  # Weekly cleanup
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Local cleanup
    local_cleanup = JournalctlClean(
        task_id="local-journal-cleanup",
        sudo=True,
        days=7,  # Keep 7 days of logs
    )

    # Remote cleanup via SSH
    remote_cleanup = JournalctlCleanSSH(
        task_id="remote-journal-cleanup",
        ssh_conn_id="production-server",
        sudo=True,
        days=7,
    )

    local_cleanup >> remote_cleanup
```

### Systemctl Service Management

Manage systemd services (start, stop, enable, disable, restart):

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import Systemctl, SystemctlSSH

with DAG(
    dag_id="service-management",
    schedule=None,  # Manual trigger
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Stop service before maintenance
    stop_worker = Systemctl(
        task_id="stop-worker",
        service="airflow-celery-worker",
        action="stop",
        sudo=True,
    )

    # Restart service after maintenance
    restart_worker = Systemctl(
        task_id="restart-worker",
        service="airflow-celery-worker",
        action="restart",
        sudo=True,
    )

    # Enable service on remote server
    enable_remote = SystemctlSSH(
        task_id="enable-remote-service",
        service="airflow-scheduler",
        action="enable",
        ssh_conn_id="production-server",
        sudo=True,
    )

    stop_worker >> restart_worker >> enable_remote
```

### Coordinated Service Restart

Stop multiple services, perform maintenance, then restart:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import Systemctl, JournalctlClean

with DAG(
    dag_id="coordinated-restart",
    schedule=timedelta(days=7),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    services = ["airflow-webserver", "airflow-scheduler", "airflow-celery-worker"]

    # Stop all services
    stop_tasks = [
        Systemctl(task_id=f"stop-{svc}", service=svc, action="stop")
        for svc in services
    ]

    # Maintenance task
    cleanup = JournalctlClean(task_id="cleanup-journals", days=7)

    # Restart all services
    start_tasks = [
        Systemctl(task_id=f"start-{svc}", service=svc, action="start")
        for svc in services
    ]

    # Chain: stop all -> cleanup -> start all
    for stop_task in stop_tasks:
        stop_task >> cleanup
    for start_task in start_tasks:
        cleanup >> start_task
```

### Reboot with Delayed Execution

Schedule reboots using the `at` command for delayed execution:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import Systemctl, Reboot, RebootSSH

with DAG(
    dag_id="graceful-reboot",
    schedule=None,  # Manual trigger
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Stop services first
    stop_worker = Systemctl(
        task_id="stop-worker",
        service="airflow-celery-worker",
        action="stop",
    )

    stop_scheduler = Systemctl(
        task_id="stop-scheduler",
        service="airflow-scheduler",
        action="stop",
    )

    # Schedule reboot in 2 minutes (to allow graceful shutdown)
    reboot = Reboot(
        task_id="scheduled-reboot",
        sudo=True,
        delay_minutes=2,
    )

    [stop_worker, stop_scheduler] >> reboot
```

### Remote Server Reboot

Reboot remote servers via SSH:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import SystemctlSSH, RebootSSH

with DAG(
    dag_id="remote-reboot",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Stop services on remote
    stop_services = SystemctlSSH(
        task_id="stop-remote-services",
        service="airflow-celery-worker",
        action="stop",
        ssh_conn_id="worker-server",
    )

    # Reboot remote server with delay
    reboot_remote = RebootSSH(
        task_id="reboot-remote",
        ssh_conn_id="worker-server",
        sudo=True,
        delay_minutes=1,
    )

    stop_services >> reboot_remote
```

### Lunchy for macOS (launchctl wrapper)

Manage macOS services using Lunchy (a friendly launchctl wrapper):

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import Lunchy, LunchySSH

with DAG(
    dag_id="macos-service-management",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Stop local macOS service
    stop_worker = Lunchy(
        task_id="stop-worker",
        service="timkpaine.airflow-celery-worker",
        action="stop",
    )

    # Start local macOS service
    start_worker = Lunchy(
        task_id="start-worker",
        service="timkpaine.airflow-celery-worker",
        action="start",
    )

    # Restart on remote Mac via SSH
    restart_remote = LunchySSH(
        task_id="restart-remote-worker",
        service="timkpaine.airflow-celery-worker",
        action="restart",
        ssh_conn_id="mac-worker",
    )

    stop_worker >> start_worker >> restart_remote
```

### macOS Graceful Reboot

Stop Lunchy-managed services before rebooting a Mac:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import Lunchy, Reboot

with DAG(
    dag_id="macos-graceful-reboot",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    services = [
        "timkpaine.airflow-celery-worker",
        "timkpaine.airflow-scheduler",
        "timkpaine.airflow-webserver",
    ]

    # Stop all services
    stop_tasks = [
        Lunchy(task_id=f"stop-{svc.split('.')[-1]}", service=svc, action="stop")
        for svc in services
    ]

    # Schedule reboot after services stop
    reboot = Reboot(
        task_id="reboot-mac",
        sudo=True,
        delay_minutes=1,
    )

    for stop_task in stop_tasks:
        stop_task >> reboot
```

## Integration with airflow-config

### YAML-Driven Library Installation

Define libraries in YAML configuration:

```yaml
# config/deploy/libraries.yaml
_target_: airflow_config.Configuration

default_args:
  _target_: airflow_config.DefaultArgs
  retries: 2
  retry_delay: 60

all_dags:
  _target_: airflow_config.DagArgs
  start_date: "2024-01-01"
  catchup: false
  schedule: "0 2 * * *"

extensions:
  libraries:
    _target_: airflow_common.LibraryList
    pip:
      - _target_: airflow_common.PipLibrary
        name: pandas
        version_constraint: ">=2.0"
      - _target_: airflow_common.PipLibrary
        name: numpy
      - _target_: airflow_common.PipLibrary
        name: scikit-learn
    git:
      - _target_: airflow_common.GitRepo
        name: my-ml-library
        repo: "https://github.com/my-org/my-ml-library.git"
        branch: main
        install: true
        editable: true
    parallel: true

dags:
  deploy-libraries:
    tasks:
      install:
        _target_: airflow_common.LibraryListTask
        task_id: install-libraries
        pip: ${extensions.libraries.pip}
        conda: []
        git: ${extensions.libraries.git}
        parallel: ${extensions.libraries.parallel}
```

```python
# dags/deploy_libraries.py
from airflow_config import load_config, DAG

config = load_config("config/deploy", "libraries")

with DAG(dag_id="deploy-libraries", config=config) as dag:
    pass  # Tasks are created from config
```

### YAML-Driven Infrastructure Tasks

```yaml
# config/infra/maintenance.yaml
_target_: airflow_config.Configuration

all_dags:
  _target_: airflow_config.DagArgs
  start_date: "2024-01-01"
  catchup: false
  schedule: "0 3 * * 0"  # Weekly on Sunday at 3 AM

dags:
  weekly-maintenance:
    tasks:
      cleanup-journals:
        _target_: airflow_common.JournalctlCleanTask
        task_id: cleanup-journals
        sudo: true
        days: 14
```

## Using Git Clone Utility

The `clone_repo` function generates bash commands for git operations:

```python
from airflow_common import clone_repo

# Generate clone/install commands
commands = clone_repo(
    name="my-repo",
    repo="https://github.com/my-org/my-repo.git",
    branch="feature/new-feature",
    clean=True,
    install=True,
    editable=True,
    tool="uv",  # Use uv for faster installs
)

# Use in a BashOperator
from airflow.operators.bash import BashOperator

clone_task = BashOperator(
    task_id="clone-and-install",
    bash_command=commands,
)
```

## Integration Notes

### airflow-pydantic

`airflow-common` is built on [airflow-pydantic](https://github.com/airflow-laminar/airflow-pydantic), which provides:

- Base Pydantic models for Airflow constructs
- Operator wrappers for serialization
- Core utilities like `fail`, `pass_`, `skip`

### airflow-config

For YAML-driven DAG definitions, use [airflow-config](https://github.com/airflow-laminar/airflow-config):

- Hydra-based configuration management
- Per-environment overrides
- Seamless integration with all `airflow-common` models

All models in `airflow-common` support Hydra's `_target_` syntax for instantiation from YAML configuration files.
