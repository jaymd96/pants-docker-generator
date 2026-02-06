"""Pure Python Dockerfile generation (no Pants dependencies).

Generates a Dockerfile for SLS distribution Docker images.
Supports the basic SLS pattern (init.sh entrypoint) and the
hook init system (entrypoint.sh lifecycle) as an opt-in mode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HealthCheckConfig:
    """Docker HEALTHCHECK configuration."""

    interval_seconds: int = 10
    timeout_seconds: int = 5
    start_period_seconds: int = 30
    retries: int = 3


@dataclass(frozen=True)
class DockerConfig:
    """Configuration for Dockerfile generation."""

    # Required
    base_image: str
    product_name: str
    product_version: str
    product_group: str
    dist_name: str  # <product-name>-<version>
    tarball_name: str  # <product-name>-<version>.sls.tgz

    # Paths
    install_path: str = "/opt/services"

    # Product metadata
    product_type: str = "helm.v1"

    # Health check (None = no HEALTHCHECK directive)
    health_check: HealthCheckConfig | None = None

    # Hook init system (bundles entrypoint.sh + hooks.sh into image)
    use_hook_init: bool = False

    # Expose ports
    expose_ports: tuple[int, ...] = ()

    # Extra labels
    labels: dict[str, str] = field(default_factory=dict)

    # Docker registry (for tagging)
    registry: str = ""

    @property
    def image_tag(self) -> str:
        """Full image tag: registry/product_name:version."""
        if self.registry:
            return f"{self.registry}/{self.product_name}:{self.product_version}"
        return f"{self.product_name}:{self.product_version}"

    @property
    def workdir(self) -> str:
        return f"{self.install_path}/{self.dist_name}"


def generate_dockerfile(config: DockerConfig) -> str:
    """Generate Dockerfile content for an SLS distribution.

    Args:
        config: Docker build configuration.

    Returns:
        Complete Dockerfile content as a string.
    """
    lines: list[str] = []

    # Header
    lines.append(f"FROM {config.base_image}")
    lines.append("")

    # OCI labels
    all_labels = {
        "org.opencontainers.image.title": config.product_name,
        "org.opencontainers.image.version": config.product_version,
        "org.opencontainers.image.vendor": config.product_group,
        "com.palantir.sls.product-type": config.product_type,
    }
    all_labels.update(config.labels)

    lines.append("LABEL \\")
    label_items = list(all_labels.items())
    for i, (key, value) in enumerate(label_items):
        suffix = " \\" if i < len(label_items) - 1 else ""
        lines.append(f'      {key}="{value}"{suffix}')
    lines.append("")

    # Add and extract tarball
    lines.append(f"ADD {config.tarball_name} {config.install_path}/")
    lines.append(f"WORKDIR {config.workdir}")
    lines.append("")

    # Create runtime directories (var/conf and var/state may not exist in tarball)
    lines.append("RUN mkdir -p var/data/tmp var/log var/run var/conf var/state")
    lines.append("")

    # Hook init system
    if config.use_hook_init:
        lines.append("# Hook init system")
        lines.append("COPY hooks/entrypoint.sh service/bin/entrypoint.sh")
        lines.append("COPY hooks/hooks.sh service/lib/hooks.sh")
        lines.append("RUN chmod +x service/bin/entrypoint.sh && \\")
        lines.append("    mkdir -p hooks/pre-configure.d hooks/configure.d \\")
        lines.append("    hooks/pre-startup.d hooks/startup.d hooks/post-startup.d \\")
        lines.append("    hooks/pre-shutdown.d hooks/shutdown.d")
        lines.append("")

    # Expose ports
    for port in config.expose_ports:
        lines.append(f"EXPOSE {port}")
    if config.expose_ports:
        lines.append("")

    # Health check
    if config.health_check is not None:
        hc = config.health_check
        lines.append(
            f"HEALTHCHECK --interval={hc.interval_seconds}s "
            f"--timeout={hc.timeout_seconds}s "
            f"--start-period={hc.start_period_seconds}s "
            f"--retries={hc.retries} \\"
        )
        lines.append("  CMD service/monitoring/bin/check.sh || exit 1")
        lines.append("")

    # Entrypoint
    if config.use_hook_init:
        lines.append('ENTRYPOINT ["service/bin/entrypoint.sh"]')
    else:
        lines.append('ENTRYPOINT ["service/bin/init.sh", "start"]')
    lines.append("")

    return "\n".join(lines)


def generate_dockerignore() -> str:
    """Generate .dockerignore content for SLS Docker builds."""
    return "\n".join([
        "# Ignore everything except the tarball and hook files",
        "**",
        "!*.sls.tgz",
        "!hooks/",
        "",
    ])
