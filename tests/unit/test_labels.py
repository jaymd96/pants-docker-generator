"""Tests for OCI label helpers."""

from pants_docker_generator._labels import oci_labels


class TestOciLabels:
    def test_basic(self):
        label = oci_labels(title="my-app", version="1.0.0")
        assert label.labels["org.opencontainers.image.title"] == "my-app"
        assert label.labels["org.opencontainers.image.version"] == "1.0.0"

    def test_omits_none(self):
        label = oci_labels(title="app")
        assert "org.opencontainers.image.version" not in label.labels
        assert "org.opencontainers.image.vendor" not in label.labels

    def test_all_fields(self):
        label = oci_labels(
            title="app",
            version="1.0",
            vendor="acme",
            description="A service",
            url="https://example.com",
            source="https://github.com/example",
            licenses="Apache-2.0",
            revision="abc123",
            created="2025-01-01T00:00:00Z",
        )
        assert len(label.labels) == 9

    def test_extra_labels(self):
        label = oci_labels(title="app", extra={"team": "platform"})
        assert label.labels["team"] == "platform"
        assert label.labels["org.opencontainers.image.title"] == "app"

    def test_extra_overrides_oci(self):
        label = oci_labels(
            title="app",
            extra={"org.opencontainers.image.title": "override"},
        )
        assert label.labels["org.opencontainers.image.title"] == "override"

    def test_renders(self):
        label = oci_labels(title="my-app")
        rendered = label.render()
        assert 'org.opencontainers.image.title="my-app"' in rendered
