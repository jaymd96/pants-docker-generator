"""Tests for Dockerfile and DockerfileBuilder."""

import pytest

from pants_docker_generator._dockerfile import Dockerfile, DockerfileBuilder
from pants_docker_generator._directives import From, Run, Workdir, Copy, BlankLine
from pants_docker_generator._stage import Stage


class TestDockerfile:
    def test_single_stage_render(self):
        stage = Stage(
            from_directive=From(image="python:3.11"),
            directives=(Run(command="echo hello"),),
        )
        df = Dockerfile(stages=(stage,))
        result = df.render()
        assert "FROM python:3.11" in result
        assert "RUN echo hello" in result
        assert result.endswith("\n")

    def test_multi_stage_render(self):
        s1 = Stage(from_directive=From(image="python:3.11", alias="builder"), directives=())
        s2 = Stage(from_directive=From(image="python:3.11-slim"), directives=())
        df = Dockerfile(stages=(s1, s2))
        result = df.render()
        assert "FROM python:3.11 AS builder" in result
        assert "FROM python:3.11-slim" in result

    def test_str(self):
        stage = Stage(from_directive=From(image="alpine"), directives=())
        df = Dockerfile(stages=(stage,))
        assert str(df) == df.render()


class TestDockerfileBuilder:
    def test_simple_build(self):
        df = (
            DockerfileBuilder()
            .from_("python:3.11-slim")
            .workdir("/app")
            .copy("requirements.txt", ".")
            .run("pip install -r requirements.txt")
            .copy(".", ".")
            .cmd("python", "app.py")
            .build()
        )
        result = df.render()
        assert "FROM python:3.11-slim" in result
        assert "WORKDIR /app" in result
        assert "COPY requirements.txt ." in result
        assert "RUN pip install -r requirements.txt" in result
        assert "COPY . ." in result
        assert 'CMD ["python", "app.py"]' in result

    def test_multi_stage(self):
        df = (
            DockerfileBuilder()
            .from_("python:3.11", alias="builder")
            .run("pip install --target=/deps -r requirements.txt")
            .from_("python:3.11-slim")
            .copy("/deps", "/usr/local/lib/", from_stage="builder")
            .entrypoint("python", "-m", "myapp")
            .build()
        )
        result = df.render()
        assert "FROM python:3.11 AS builder" in result
        assert "FROM python:3.11-slim" in result
        assert "COPY --from=builder /deps /usr/local/lib/" in result

    def test_all_directives(self):
        df = (
            DockerfileBuilder()
            .from_("ubuntu:22.04", platform="linux/amd64")
            .arg("VERSION")
            .env("APP_ENV", "production")
            .label({"maintainer": "team"})
            .user("nobody", "nogroup")
            .workdir("/app")
            .add("archive.tar.gz", "/opt/")
            .copy("src/", "/app/src/")
            .run("apt-get update")
            .expose(8080)
            .expose(53, "udp")
            .volume("/data")
            .shell("/bin/bash", "-c")
            .healthcheck("curl -f http://localhost/")
            .entrypoint("python")
            .cmd("-m", "app")
            .build()
        )
        result = df.render()
        assert "FROM --platform=linux/amd64 ubuntu:22.04" in result
        assert "ARG VERSION" in result
        assert 'ENV APP_ENV="production"' in result
        assert 'maintainer="team"' in result
        assert "USER nobody:nogroup" in result
        assert "WORKDIR /app" in result
        assert "ADD archive.tar.gz /opt/" in result
        assert "COPY src/ /app/src/" in result
        assert "RUN apt-get update" in result
        assert "EXPOSE 8080" in result
        assert "EXPOSE 53/udp" in result
        assert "VOLUME /data" in result
        assert 'SHELL ["/bin/bash", "-c"]' in result
        assert "HEALTHCHECK" in result
        assert 'ENTRYPOINT ["python"]' in result
        assert 'CMD ["-m", "app"]' in result

    def test_blank_and_comment(self):
        df = (
            DockerfileBuilder()
            .from_("alpine")
            .comment("Install packages")
            .run("apk add curl")
            .blank()
            .run("apk add git")
            .build()
        )
        result = df.render()
        assert "# Install packages" in result
        lines = result.split("\n")
        # Find the blank line
        blank_indices = [i for i, l in enumerate(lines) if l == ""]
        assert len(blank_indices) >= 1

    def test_healthcheck_none(self):
        df = (
            DockerfileBuilder()
            .from_("alpine")
            .healthcheck_none()
            .build()
        )
        assert "HEALTHCHECK NONE" in df.render()

    def test_directive_method(self):
        df = (
            DockerfileBuilder()
            .from_("alpine")
            .directive(Run(command="echo custom"))
            .build()
        )
        assert "RUN echo custom" in df.render()

    def test_build_no_stages_raises(self):
        with pytest.raises(ValueError, match="at least one FROM"):
            DockerfileBuilder().build()

    def test_three_stages(self):
        df = (
            DockerfileBuilder()
            .from_("node:18", alias="frontend")
            .run("npm build")
            .from_("python:3.11", alias="backend")
            .run("pip install .")
            .from_("nginx:alpine")
            .copy("/frontend/dist", "/usr/share/nginx/html", from_stage="frontend")
            .build()
        )
        assert len(df.stages) == 3
        assert df.stages[0].alias == "frontend"
        assert df.stages[1].alias == "backend"
        assert df.stages[2].alias is None
