"""Tests for Dockerfile generation (pure functions, no Pants engine)."""

from __future__ import annotations

import pytest

from pants_docker_generator._dockerfile import (
    DockerConfig,
    HealthCheckConfig,
    generate_dockerfile,
    generate_dockerignore,
)


# =============================================================================
# Helpers
# =============================================================================


def _make_config(**overrides) -> DockerConfig:
    """Create a DockerConfig with sensible defaults."""
    defaults = dict(
        base_image="python:3.11-slim",
        product_name="my-service",
        product_version="1.0.0",
        product_group="com.example",
        dist_name="my-service-1.0.0",
        tarball_name="my-service-1.0.0.sls.tgz",
    )
    defaults.update(overrides)
    return DockerConfig(**defaults)


# =============================================================================
# DockerConfig tests
# =============================================================================


class TestDockerConfig:
    """Test DockerConfig dataclass."""

    def test_image_tag_with_registry(self):
        config = _make_config(registry="registry.example.io")
        assert config.image_tag == "registry.example.io/my-service:1.0.0"

    def test_image_tag_without_registry(self):
        config = _make_config(registry="")
        assert config.image_tag == "my-service:1.0.0"

    def test_workdir(self):
        config = _make_config(install_path="/opt/services")
        assert config.workdir == "/opt/services/my-service-1.0.0"

    def test_custom_install_path(self):
        config = _make_config(install_path="/app")
        assert config.workdir == "/app/my-service-1.0.0"

    def test_frozen(self):
        config = _make_config()
        with pytest.raises(AttributeError):
            config.base_image = "other"  # type: ignore[misc]


# =============================================================================
# HealthCheckConfig tests
# =============================================================================


class TestHealthCheckConfig:
    """Test HealthCheckConfig defaults."""

    def test_defaults(self):
        hc = HealthCheckConfig()
        assert hc.interval_seconds == 10
        assert hc.timeout_seconds == 5
        assert hc.start_period_seconds == 30
        assert hc.retries == 3

    def test_custom_values(self):
        hc = HealthCheckConfig(
            interval_seconds=30,
            timeout_seconds=10,
            start_period_seconds=60,
            retries=5,
        )
        assert hc.interval_seconds == 30
        assert hc.retries == 5


# =============================================================================
# Dockerfile generation tests
# =============================================================================


class TestGenerateDockerfileBasic:
    """Test basic Dockerfile structure."""

    def test_starts_with_from(self):
        config = _make_config()
        dockerfile = generate_dockerfile(config)
        assert dockerfile.startswith("FROM python:3.11-slim\n")

    def test_custom_base_image(self):
        config = _make_config(base_image="ubuntu:22.04")
        dockerfile = generate_dockerfile(config)
        assert "FROM ubuntu:22.04" in dockerfile

    def test_contains_add_tarball(self):
        config = _make_config()
        dockerfile = generate_dockerfile(config)
        assert "ADD my-service-1.0.0.sls.tgz /opt/services/" in dockerfile

    def test_contains_workdir(self):
        config = _make_config()
        dockerfile = generate_dockerfile(config)
        assert "WORKDIR /opt/services/my-service-1.0.0" in dockerfile

    def test_custom_install_path(self):
        config = _make_config(install_path="/app")
        dockerfile = generate_dockerfile(config)
        assert "ADD my-service-1.0.0.sls.tgz /app/" in dockerfile
        assert "WORKDIR /app/my-service-1.0.0" in dockerfile

    def test_creates_runtime_dirs(self):
        config = _make_config()
        dockerfile = generate_dockerfile(config)
        assert "RUN mkdir -p var/data/tmp var/log var/run var/conf var/state" in dockerfile

    def test_default_entrypoint(self):
        config = _make_config()
        dockerfile = generate_dockerfile(config)
        assert 'ENTRYPOINT ["service/bin/init.sh", "start"]' in dockerfile


# =============================================================================
# OCI Labels
# =============================================================================


class TestDockerfileLabels:
    """Test OCI label generation."""

    def test_contains_standard_labels(self):
        config = _make_config()
        dockerfile = generate_dockerfile(config)
        assert 'org.opencontainers.image.title="my-service"' in dockerfile
        assert 'org.opencontainers.image.version="1.0.0"' in dockerfile
        assert 'org.opencontainers.image.vendor="com.example"' in dockerfile
        assert 'com.palantir.sls.product-type="helm.v1"' in dockerfile

    def test_custom_product_type(self):
        config = _make_config(product_type="service.v1")
        dockerfile = generate_dockerfile(config)
        assert 'com.palantir.sls.product-type="service.v1"' in dockerfile

    def test_extra_labels(self):
        config = _make_config(labels={"team": "platform", "env": "prod"})
        dockerfile = generate_dockerfile(config)
        assert 'team="platform"' in dockerfile
        assert 'env="prod"' in dockerfile


# =============================================================================
# Health Check
# =============================================================================


class TestDockerfileHealthCheck:
    """Test HEALTHCHECK directive generation."""

    def test_no_healthcheck_by_default(self):
        config = _make_config(health_check=None)
        dockerfile = generate_dockerfile(config)
        assert "HEALTHCHECK" not in dockerfile

    def test_healthcheck_with_defaults(self):
        config = _make_config(health_check=HealthCheckConfig())
        dockerfile = generate_dockerfile(config)
        assert "HEALTHCHECK" in dockerfile
        assert "--interval=10s" in dockerfile
        assert "--timeout=5s" in dockerfile
        assert "--start-period=30s" in dockerfile
        assert "--retries=3" in dockerfile
        assert "service/monitoring/bin/check.sh || exit 1" in dockerfile

    def test_custom_healthcheck(self):
        hc = HealthCheckConfig(
            interval_seconds=30,
            timeout_seconds=10,
            start_period_seconds=60,
            retries=5,
        )
        config = _make_config(health_check=hc)
        dockerfile = generate_dockerfile(config)
        assert "--interval=30s" in dockerfile
        assert "--timeout=10s" in dockerfile
        assert "--start-period=60s" in dockerfile
        assert "--retries=5" in dockerfile


# =============================================================================
# Hook Init System
# =============================================================================


class TestDockerfileHookInit:
    """Test hook init system integration."""

    def test_no_hooks_by_default(self):
        config = _make_config(use_hook_init=False)
        dockerfile = generate_dockerfile(config)
        assert "entrypoint.sh" not in dockerfile
        assert "hooks.sh" not in dockerfile

    def test_hook_init_copies_files(self):
        config = _make_config(use_hook_init=True)
        dockerfile = generate_dockerfile(config)
        assert "COPY hooks/entrypoint.sh service/bin/entrypoint.sh" in dockerfile
        assert "COPY hooks/hooks.sh service/lib/hooks.sh" in dockerfile

    def test_hook_init_creates_hook_dirs(self):
        config = _make_config(use_hook_init=True)
        dockerfile = generate_dockerfile(config)
        assert "hooks/pre-configure.d" in dockerfile
        assert "hooks/startup.d" in dockerfile
        assert "hooks/shutdown.d" in dockerfile

    def test_hook_init_changes_entrypoint(self):
        config = _make_config(use_hook_init=True)
        dockerfile = generate_dockerfile(config)
        assert 'ENTRYPOINT ["service/bin/entrypoint.sh"]' in dockerfile
        assert 'ENTRYPOINT ["service/bin/init.sh", "start"]' not in dockerfile

    def test_default_entrypoint_without_hooks(self):
        config = _make_config(use_hook_init=False)
        dockerfile = generate_dockerfile(config)
        assert 'ENTRYPOINT ["service/bin/init.sh", "start"]' in dockerfile


# =============================================================================
# Port Exposure
# =============================================================================


class TestDockerfileExpose:
    """Test EXPOSE directive generation."""

    def test_no_expose_by_default(self):
        config = _make_config()
        dockerfile = generate_dockerfile(config)
        assert "EXPOSE" not in dockerfile

    def test_single_port(self):
        config = _make_config(expose_ports=(8080,))
        dockerfile = generate_dockerfile(config)
        assert "EXPOSE 8080" in dockerfile

    def test_multiple_ports(self):
        config = _make_config(expose_ports=(8080, 8443, 9090))
        dockerfile = generate_dockerfile(config)
        assert "EXPOSE 8080" in dockerfile
        assert "EXPOSE 8443" in dockerfile
        assert "EXPOSE 9090" in dockerfile


# =============================================================================
# Full Integration
# =============================================================================


class TestDockerfileIntegration:
    """Test complete Dockerfile generation scenarios."""

    def test_minimal_service(self):
        """Minimal service with no health check, no hooks."""
        config = _make_config()
        dockerfile = generate_dockerfile(config)

        # Must have FROM, ADD, WORKDIR, ENTRYPOINT
        assert "FROM python:3.11-slim" in dockerfile
        assert "ADD my-service-1.0.0.sls.tgz" in dockerfile
        assert "WORKDIR /opt/services/my-service-1.0.0" in dockerfile
        assert "ENTRYPOINT" in dockerfile

        # Must NOT have HEALTHCHECK, EXPOSE, hooks
        assert "HEALTHCHECK" not in dockerfile
        assert "EXPOSE" not in dockerfile
        assert "hooks.sh" not in dockerfile

    def test_full_production_service(self):
        """Full production service with all features."""
        config = DockerConfig(
            base_image="python:3.11-slim",
            product_name="api-gateway",
            product_version="2.5.0",
            product_group="com.example.platform",
            dist_name="api-gateway-2.5.0",
            tarball_name="api-gateway-2.5.0.sls.tgz",
            install_path="/opt/services",
            product_type="helm.v1",
            health_check=HealthCheckConfig(
                interval_seconds=15,
                timeout_seconds=10,
                start_period_seconds=45,
            ),
            use_hook_init=True,
            expose_ports=(8080, 8443),
            labels={"team": "platform", "tier": "frontend"},
            registry="registry.example.io",
        )

        dockerfile = generate_dockerfile(config)

        # All sections present
        assert "FROM python:3.11-slim" in dockerfile
        assert "LABEL" in dockerfile
        assert 'team="platform"' in dockerfile
        assert "ADD api-gateway-2.5.0.sls.tgz /opt/services/" in dockerfile
        assert "WORKDIR /opt/services/api-gateway-2.5.0" in dockerfile
        assert "entrypoint.sh" in dockerfile
        assert "hooks.sh" in dockerfile
        assert "EXPOSE 8080" in dockerfile
        assert "EXPOSE 8443" in dockerfile
        assert "HEALTHCHECK" in dockerfile
        assert "--interval=15s" in dockerfile
        assert 'ENTRYPOINT ["service/bin/entrypoint.sh"]' in dockerfile

    def test_image_tag_in_output(self):
        """Verify the image tag is correctly formed."""
        config = DockerConfig(
            base_image="python:3.11-slim",
            product_name="my-api",
            product_version="3.0.0-rc1",
            product_group="com.example",
            dist_name="my-api-3.0.0-rc1",
            tarball_name="my-api-3.0.0-rc1.sls.tgz",
            registry="ghcr.io/myorg",
        )
        assert config.image_tag == "ghcr.io/myorg/my-api:3.0.0-rc1"


# =============================================================================
# Dockerignore
# =============================================================================


class TestGenerateDockerignore:
    """Test .dockerignore generation."""

    def test_ignores_everything_except_tarball(self):
        content = generate_dockerignore()
        assert "**" in content
        assert "!*.sls.tgz" in content

    def test_allows_hooks_directory(self):
        content = generate_dockerignore()
        assert "!hooks/" in content
