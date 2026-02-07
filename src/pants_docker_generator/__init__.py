"""General-purpose Dockerfile generation library.

Three levels of abstraction:

1. **Directives** -- individual Dockerfile instructions as dataclasses
2. **Dockerfile + DockerfileBuilder** -- assembles directives into stages
3. **Presets** -- one-call functions for common patterns (e.g. SLS)
"""

from pants_docker_generator._directives import (
    Add,
    Arg,
    BlankLine,
    Cmd,
    Comment,
    Copy,
    Directive,
    Entrypoint,
    Env,
    Expose,
    From,
    HealthCheck,
    HealthCheckNone,
    Label,
    Run,
    Shell,
    User,
    Volume,
    Workdir,
)
from pants_docker_generator._dockerfile import Dockerfile, DockerfileBuilder
from pants_docker_generator._dockerignore import DockerignoreConfig, generate_dockerignore
from pants_docker_generator._labels import oci_labels
from pants_docker_generator._presets import sls_dockerfile, sls_dockerignore
from pants_docker_generator._stage import Stage

__all__ = [
    # Directives
    "Add",
    "Arg",
    "BlankLine",
    "Cmd",
    "Comment",
    "Copy",
    "Directive",
    "Entrypoint",
    "Env",
    "Expose",
    "From",
    "HealthCheck",
    "HealthCheckNone",
    "Label",
    "Run",
    "Shell",
    "User",
    "Volume",
    "Workdir",
    # Assembly
    "Dockerfile",
    "DockerfileBuilder",
    "Stage",
    # Dockerignore
    "DockerignoreConfig",
    "generate_dockerignore",
    # Labels
    "oci_labels",
    # Presets
    "sls_dockerfile",
    "sls_dockerignore",
]
