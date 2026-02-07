"""Tests for Stage dataclass."""

from pants_docker_generator._stage import Stage
from pants_docker_generator._directives import From, Run, Workdir


class TestStage:
    def test_render_empty(self):
        stage = Stage(from_directive=From(image="alpine"))
        assert stage.render() == "FROM alpine"

    def test_render_with_directives(self):
        stage = Stage(
            from_directive=From(image="python:3.11", alias="build"),
            directives=(
                Workdir(path="/app"),
                Run(command="pip install ."),
            ),
        )
        result = stage.render()
        assert "FROM python:3.11 AS build" in result
        assert "WORKDIR /app" in result
        assert "RUN pip install ." in result

    def test_alias_property(self):
        assert Stage(from_directive=From(image="alpine", alias="base")).alias == "base"
        assert Stage(from_directive=From(image="alpine")).alias is None
