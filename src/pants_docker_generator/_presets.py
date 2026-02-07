"""Pre-built Dockerfile presets for common patterns.

These reproduce well-known Dockerfile layouts in a single function call.
"""

from pants_docker_generator._directives import (
    Add,
    BlankLine,
    Comment,
    Copy,
    Entrypoint,
    Expose,
    HealthCheck,
    Label,
    Run,
    Workdir,
)
from pants_docker_generator._dockerfile import Dockerfile, DockerfileBuilder
from pants_docker_generator._dockerignore import generate_dockerignore


def sls_dockerfile(
    *,
    base_image: str,
    product_name: str,
    product_version: str,
    product_group: str,
    dist_name: str,
    tarball_name: str,
    install_path: str = "/opt/services",
    product_type: str = "helm.v1",
    health_check_interval: int | None = None,
    health_check_timeout: int | None = None,
    health_check_start_period: int | None = None,
    health_check_retries: int | None = None,
    use_hook_init: bool = False,
    expose_ports: tuple[int, ...] = (),
    labels: dict[str, str] | None = None,
) -> Dockerfile:
    """Generate a Dockerfile for an SLS distribution.

    This reproduces the exact layout previously produced by the old
    ``DockerConfig`` + ``generate_dockerfile()`` API.
    """
    workdir = f"{install_path}/{dist_name}"

    # Build labels
    all_labels = {
        "org.opencontainers.image.title": product_name,
        "org.opencontainers.image.version": product_version,
        "org.opencontainers.image.vendor": product_group,
        "com.palantir.sls.product-type": product_type,
    }
    if labels:
        all_labels.update(labels)

    b = DockerfileBuilder().from_(base_image).blank()

    # Labels
    b.label(all_labels).blank()

    # Add and extract tarball
    b.add(tarball_name, f"{install_path}/")
    b.workdir(workdir).blank()

    # Create runtime directories
    b.run("mkdir -p var/data/tmp var/log var/run var/conf var/state").blank()

    # Hook init system
    if use_hook_init:
        b.comment("Hook init system")
        b.copy("hooks/entrypoint.sh", "service/bin/entrypoint.sh")
        b.copy("hooks/hooks.sh", "service/lib/hooks.sh")
        b.run(
            "chmod +x service/bin/entrypoint.sh && \\\n"
            "    mkdir -p hooks/pre-configure.d hooks/configure.d \\\n"
            "    hooks/pre-startup.d hooks/startup.d hooks/post-startup.d \\\n"
            "    hooks/pre-shutdown.d hooks/shutdown.d"
        )
        b.blank()

    # Expose ports
    for port in expose_ports:
        b.expose(port)
    if expose_ports:
        b.blank()

    # Health check
    has_health_check = health_check_interval is not None or health_check_timeout is not None
    if has_health_check:
        b.healthcheck(
            "service/monitoring/bin/check.sh || exit 1",
            interval_seconds=health_check_interval or 10,
            timeout_seconds=health_check_timeout or 5,
            start_period_seconds=health_check_start_period or 30,
            retries=health_check_retries or 3,
        )
        b.blank()

    # Entrypoint
    if use_hook_init:
        b.entrypoint("service/bin/entrypoint.sh")
    else:
        b.entrypoint("service/bin/init.sh", "start")
    b.blank()

    return b.build()


def sls_dockerignore() -> str:
    """Generate a .dockerignore for SLS Docker builds."""
    return generate_dockerignore(
        allow=("*.sls.tgz", "hooks/"),
        comment="Ignore everything except the tarball and hook files",
    )
