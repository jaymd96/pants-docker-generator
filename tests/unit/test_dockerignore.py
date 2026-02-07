"""Tests for dockerignore generation."""

from pants_docker_generator._dockerignore import DockerignoreConfig, generate_dockerignore


class TestDockerignoreConfig:
    def test_default_ignore_all(self):
        config = DockerignoreConfig()
        result = config.render()
        assert "**" in result

    def test_allow_patterns(self):
        config = DockerignoreConfig(allow_patterns=("*.tgz", "hooks/"))
        result = config.render()
        assert "!*.tgz" in result
        assert "!hooks/" in result

    def test_comment(self):
        config = DockerignoreConfig(comment="Only allow tarballs")
        result = config.render()
        assert "# Only allow tarballs" in result

    def test_deny_patterns(self):
        config = DockerignoreConfig(ignore_all=False, deny_patterns=("*.log", "tmp/"))
        result = config.render()
        assert "*.log" in result
        assert "tmp/" in result
        assert "**" not in result


class TestGenerateDockerignore:
    def test_basic(self):
        result = generate_dockerignore(allow=("dist/",))
        assert "**" in result
        assert "!dist/" in result

    def test_with_comment(self):
        result = generate_dockerignore(allow=("app.py",), comment="Test")
        assert "# Test" in result
        assert "!app.py" in result
