# Getting Started

## Overview

`airflow-common` provides a collection of **common operators, tasks, and utilities** for Apache Airflow that simplify everyday workflow development. It includes reusable components for topology management, library installation, infrastructure maintenance, and common task patterns.

**Key Features:**

- **Common Operators**: Pre-built `Skip`, `Fail`, and `Pass` operators for workflow control
- **Topology Helpers**: Functions like `all_success_any_failure` and `if_booted_do` for complex DAG topologies
- **Library Management**: Models and operators for installing pip, conda, and git libraries
- **Infrastructure Tasks**: Common infrastructure tasks like journal cleanup
- **Pydantic Integration**: All models are Pydantic-based for validation and serialization

> [!NOTE]
> This library is built on [airflow-pydantic](https://github.com/airflow-laminar/airflow-pydantic) and integrates seamlessly with [airflow-config](https://github.com/airflow-laminar/airflow-config) for YAML-driven DAG definitions.

## Installation

Install airflow-common from PyPI:

```bash
pip install airflow-common
```

Or via conda:

```bash
conda install airflow-common -c conda-forge
```

For use with Apache Airflow 2.x:

```bash
pip install airflow-common[airflow]
```

For use with Apache Airflow 3.x:

```bash
pip install airflow-common[airflow3]
```

## Basic Usage

### Common Operators

Use the convenience operators for common workflow patterns:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow_common import Skip, Fail, Pass

with DAG(
    dag_id="common-operators-example",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Create a skip task (useful for conditional branches)
    skip_task = Skip(task_id="skip-this")

    # Create a fail task (useful for error handling branches)
    fail_task = Fail(task_id="fail-on-error", trigger_rule="one_failed")

    # Create a pass task (useful for success branches)
    pass_task = Pass(task_id="success-path", trigger_rule="none_failed")
```

### Topology Helpers

Build complex DAG topologies with helper functions:

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow_common import all_success_any_failure

with DAG(
    dag_id="topology-example",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Create multiple tasks
    tasks = [
        PythonOperator(task_id=f"task-{i}", python_callable=lambda: None)
        for i in range(3)
    ]

    # Create success/failure aggregation
    any_failure, all_success = all_success_any_failure(
        task_id="aggregation",
        tasks=tasks,
        dag=dag,
    )
```

### Library Models

Define libraries to install with Pydantic models:

```python
from airflow_common import PipLibrary, GitRepo, LibraryList

# Define pip libraries
pandas = PipLibrary(name="pandas", version_constraint=">=2.0")
numpy = PipLibrary(name="numpy")

# Define a git repository to clone and install
my_lib = GitRepo(
    name="my-library",
    repo="https://github.com/my-org/my-library.git",
    branch="main",
    install=True,
    editable=True,
)

# Group them in a library list
libraries = LibraryList(
    pip=[pandas, numpy],
    git=[my_lib],
)
```

## Module Structure

### `airflow` Module

Common Airflow operators and topology helpers:

- `Skip`, `Fail`, `Pass` - Convenience operators
- `all_success_any_failure` - Aggregate success/failure from multiple tasks
- `if_booted_do` - Conditional execution based on host availability

### `library` Module

Library management models and operators:

- `PipLibrary` - Pip package installation model
- `CondaLibrary` - Conda package installation model
- `GitRepo` - Git repository clone and install model
- `LibraryList` - Aggregate library list
- `InstallLibraryOperator` - Operator to install libraries locally
- `InstallLibrarySSHOperator` - Operator to install libraries via SSH

### `infra` Module

Infrastructure maintenance tasks:

- `JournalctlClean` / `JournalctlCleanSSH` - Clean systemd journal logs
- `Systemctl` / `SystemctlSSH` - Manage systemd services (start, stop, enable, disable, restart)
- `Reboot` / `RebootSSH` - Reboot systems (with optional delay via `at` command)
- `Lunchy` / `LunchySSH` - Manage macOS launchd services via Lunchy

## Integration with airflow-config

Define libraries and tasks in YAML with [airflow-config](https://github.com/airflow-laminar/airflow-config):

```yaml
# config/libraries.yaml
_target_: airflow_config.Configuration

extensions:
  libraries:
    _target_: airflow_common.LibraryList
    pip:
      - _target_: airflow_common.PipLibrary
        name: pandas
        version_constraint: ">=2.0"
      - _target_: airflow_common.PipLibrary
        name: numpy
    git:
      - _target_: airflow_common.GitRepo
        name: my-library
        repo: "https://github.com/my-org/my-library.git"
        branch: main
        install: true
        editable: true
```

## Next Steps

- See [Examples](examples.md) for more detailed use cases
- Consult the [API Reference](API.md) for complete API documentation
- Check out [airflow-pydantic](https://github.com/airflow-laminar/airflow-pydantic) for core Pydantic Airflow models
