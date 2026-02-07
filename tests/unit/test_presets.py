"""Tests for SLS preset functions."""

from pants_docker_generator._presets import sls_dockerfile, sls_dockerignore


class TestSlsDockerfile:
    def test_basic_output(self):
        df = sls_dockerfile(
            base_image="python:3.11-slim",
            product_name="my-service",
            product_version="1.0.0",
            product_group="com.example",
            dist_name="my-service-1.0.0",
            tarball_name="my-service-1.0.0.sls.tgz",
        )
        result = df.render()
        assert "FROM python:3.11-slim" in result
        assert 'org.opencontainers.image.title="my-service"' in result
        assert 'org.opencontainers.image.version="1.0.0"' in result
        assert 'org.opencontainers.image.vendor="com.example"' in result
        assert 'com.palantir.sls.product-type="helm.v1"' in result
        assert "ADD my-service-1.0.0.sls.tgz /opt/services/" in result
        assert "WORKDIR /opt/services/my-service-1.0.0" in result
        assert "RUN mkdir -p var/data/tmp var/log var/run var/conf var/state" in result
        assert 'ENTRYPOINT ["service/bin/init.sh", "start"]' in result

    def test_custom_install_path(self):
        df = sls_dockerfile(
            base_image="python:3.11-slim",
            product_name="svc",
            product_version="1.0.0",
            product_group="com.example",
            dist_name="svc-1.0.0",
            tarball_name="svc-1.0.0.sls.tgz",
            install_path="/app",
        )
        result = df.render()
        assert "ADD svc-1.0.0.sls.tgz /app/" in result
        assert "WORKDIR /app/svc-1.0.0" in result

    def test_hook_init(self):
        df = sls_dockerfile(
            base_image="python:3.11-slim",
            product_name="svc",
            product_version="1.0.0",
            product_group="com.example",
            dist_name="svc-1.0.0",
            tarball_name="svc-1.0.0.sls.tgz",
            use_hook_init=True,
        )
        result = df.render()
        assert "COPY hooks/entrypoint.sh service/bin/entrypoint.sh" in result
        assert "COPY hooks/hooks.sh service/lib/hooks.sh" in result
        assert 'ENTRYPOINT ["service/bin/entrypoint.sh"]' in result

    def test_expose_ports(self):
        df = sls_dockerfile(
            base_image="python:3.11-slim",
            product_name="svc",
            product_version="1.0.0",
            product_group="com.example",
            dist_name="svc-1.0.0",
            tarball_name="svc-1.0.0.sls.tgz",
            expose_ports=(8080, 8443),
        )
        result = df.render()
        assert "EXPOSE 8080" in result
        assert "EXPOSE 8443" in result

    def test_health_check(self):
        df = sls_dockerfile(
            base_image="python:3.11-slim",
            product_name="svc",
            product_version="1.0.0",
            product_group="com.example",
            dist_name="svc-1.0.0",
            tarball_name="svc-1.0.0.sls.tgz",
            health_check_interval=15,
            health_check_timeout=10,
        )
        result = df.render()
        assert "HEALTHCHECK" in result
        assert "--interval=15s" in result
        assert "--timeout=10s" in result
        assert "service/monitoring/bin/check.sh || exit 1" in result

    def test_extra_labels(self):
        df = sls_dockerfile(
            base_image="python:3.11-slim",
            product_name="svc",
            product_version="1.0.0",
            product_group="com.example",
            dist_name="svc-1.0.0",
            tarball_name="svc-1.0.0.sls.tgz",
            labels={"team": "platform"},
        )
        result = df.render()
        assert 'team="platform"' in result

    def test_no_healthcheck_by_default(self):
        df = sls_dockerfile(
            base_image="python:3.11-slim",
            product_name="svc",
            product_version="1.0.0",
            product_group="com.example",
            dist_name="svc-1.0.0",
            tarball_name="svc-1.0.0.sls.tgz",
        )
        result = df.render()
        assert "HEALTHCHECK" not in result

    def test_no_hooks_by_default(self):
        df = sls_dockerfile(
            base_image="python:3.11-slim",
            product_name="svc",
            product_version="1.0.0",
            product_group="com.example",
            dist_name="svc-1.0.0",
            tarball_name="svc-1.0.0.sls.tgz",
        )
        result = df.render()
        assert "hooks.sh" not in result
        assert "entrypoint.sh" not in result


class TestSlsDockerignore:
    def test_content(self):
        result = sls_dockerignore()
        assert "**" in result
        assert "!*.sls.tgz" in result
        assert "!hooks/" in result
        assert "# Ignore everything except the tarball and hook files" in result
