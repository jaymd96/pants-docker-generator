"""Tests for individual Dockerfile directive rendering."""

import pytest

from pants_docker_generator._directives import (
    Add,
    Arg,
    BlankLine,
    Cmd,
    Comment,
    Copy,
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


class TestFrom:
    def test_basic(self):
        assert From(image="python:3.11").render() == "FROM python:3.11"

    def test_with_alias(self):
        assert From(image="python:3.11", alias="builder").render() == "FROM python:3.11 AS builder"

    def test_with_platform(self):
        assert From(image="python:3.11", platform="linux/amd64").render() == "FROM --platform=linux/amd64 python:3.11"

    def test_with_platform_and_alias(self):
        assert From(image="python:3.11", platform="linux/amd64", alias="build").render() == "FROM --platform=linux/amd64 python:3.11 AS build"


class TestRun:
    def test_basic(self):
        assert Run(command="apt-get update").render() == "RUN apt-get update"

    def test_multiline(self):
        cmd = "apt-get update && \\\n    apt-get install -y curl"
        assert Run(command=cmd).render() == f"RUN {cmd}"


class TestCopy:
    def test_basic(self):
        assert Copy(src=".", dst="/app").render() == "COPY . /app"

    def test_from_stage(self):
        assert Copy(src="/build/out", dst="/app", from_stage="builder").render() == "COPY --from=builder /build/out /app"

    def test_chown(self):
        assert Copy(src=".", dst="/app", chown="1000:1000").render() == "COPY --chown=1000:1000 . /app"


class TestAdd:
    def test_basic(self):
        assert Add(src="app.tar.gz", dst="/opt/").render() == "ADD app.tar.gz /opt/"

    def test_chown(self):
        assert Add(src="app.tar.gz", dst="/opt/", chown="root").render() == "ADD --chown=root app.tar.gz /opt/"


class TestWorkdir:
    def test_basic(self):
        assert Workdir(path="/app").render() == "WORKDIR /app"


class TestUser:
    def test_user_only(self):
        assert User(user="nobody").render() == "USER nobody"

    def test_user_and_group(self):
        assert User(user="app", group="app").render() == "USER app:app"


class TestExpose:
    def test_basic(self):
        assert Expose(port=8080).render() == "EXPOSE 8080"

    def test_with_protocol(self):
        assert Expose(port=53, protocol="udp").render() == "EXPOSE 53/udp"


class TestEntrypoint:
    def test_single_arg(self):
        assert Entrypoint(args=("python",)).render() == 'ENTRYPOINT ["python"]'

    def test_multiple_args(self):
        assert Entrypoint(args=("python", "-m", "app")).render() == 'ENTRYPOINT ["python", "-m", "app"]'


class TestCmd:
    def test_single_arg(self):
        assert Cmd(args=("python",)).render() == 'CMD ["python"]'

    def test_multiple_args(self):
        assert Cmd(args=("python", "app.py")).render() == 'CMD ["python", "app.py"]'


class TestArg:
    def test_no_default(self):
        assert Arg(name="VERSION").render() == "ARG VERSION"

    def test_with_default(self):
        assert Arg(name="VERSION", default="1.0").render() == "ARG VERSION=1.0"


class TestEnv:
    def test_basic(self):
        assert Env(key="APP_ENV", value="production").render() == 'ENV APP_ENV="production"'


class TestLabel:
    def test_single(self):
        assert Label(labels={"version": "1.0"}).render() == 'LABEL version="1.0"'

    def test_multiple(self):
        result = Label(labels={"a": "1", "b": "2"}).render()
        assert result.startswith("LABEL \\")
        assert 'a="1"' in result
        assert 'b="2"' in result

    def test_empty(self):
        assert Label(labels={}).render() == ""


class TestVolume:
    def test_single(self):
        assert Volume(paths=("/data",)).render() == "VOLUME /data"

    def test_multiple(self):
        assert Volume(paths=("/data", "/logs")).render() == 'VOLUME ["/data", "/logs"]'


class TestShell:
    def test_basic(self):
        assert Shell(args=("/bin/bash", "-c")).render() == 'SHELL ["/bin/bash", "-c"]'


class TestHealthCheck:
    def test_defaults(self):
        result = HealthCheck(command="curl -f http://localhost/").render()
        assert "--interval=10s" in result
        assert "--timeout=5s" in result
        assert "--start-period=30s" in result
        assert "--retries=3" in result
        assert "CMD curl -f http://localhost/" in result

    def test_custom(self):
        result = HealthCheck(command="test", interval_seconds=30, retries=5).render()
        assert "--interval=30s" in result
        assert "--retries=5" in result


class TestHealthCheckNone:
    def test_render(self):
        assert HealthCheckNone().render() == "HEALTHCHECK NONE"


class TestComment:
    def test_basic(self):
        assert Comment(text="Install deps").render() == "# Install deps"


class TestBlankLine:
    def test_render(self):
        assert BlankLine().render() == ""
