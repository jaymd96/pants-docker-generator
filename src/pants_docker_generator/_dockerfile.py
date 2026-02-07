"""Dockerfile and DockerfileBuilder - the core assembly API."""

from dataclasses import dataclass, field

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
    Directive,
)
from pants_docker_generator._stage import Stage


@dataclass(frozen=True)
class Dockerfile:
    """An immutable representation of a complete Dockerfile."""

    stages: tuple[Stage, ...]

    def render(self) -> str:
        """Render the full Dockerfile as a string."""
        parts = []
        for i, stage in enumerate(self.stages):
            if i > 0:
                parts.append("")  # blank line between stages
            parts.append(stage.render())
        result = "\n".join(parts)
        if not result.endswith("\n"):
            result += "\n"
        return result

    def __str__(self) -> str:
        return self.render()


class DockerfileBuilder:
    """Fluent builder for constructing Dockerfiles.

    Usage::

        df = (DockerfileBuilder()
            .from_("python:3.11-slim")
            .workdir("/app")
            .copy("requirements.txt", ".")
            .run("pip install --no-cache-dir -r requirements.txt")
            .copy(".", ".")
            .expose(8080)
            .cmd("python", "app.py")
            .build())
    """

    def __init__(self) -> None:
        self._stages: list[Stage] = []
        self._current_from: From | None = None
        self._current_directives: list[Directive] = []

    def _flush_stage(self) -> None:
        """Flush the current stage to the stages list."""
        if self._current_from is not None:
            self._stages.append(Stage(
                from_directive=self._current_from,
                directives=tuple(self._current_directives),
            ))
            self._current_from = None
            self._current_directives = []

    def from_(
        self,
        image: str,
        *,
        alias: str | None = None,
        platform: str | None = None,
    ) -> "DockerfileBuilder":
        """Start a new stage with FROM."""
        self._flush_stage()
        self._current_from = From(image=image, alias=alias, platform=platform)
        return self

    def run(self, command: str) -> "DockerfileBuilder":
        self._current_directives.append(Run(command=command))
        return self

    def copy(
        self,
        src: str,
        dst: str,
        *,
        from_stage: str | None = None,
        chown: str | None = None,
    ) -> "DockerfileBuilder":
        self._current_directives.append(Copy(src=src, dst=dst, from_stage=from_stage, chown=chown))
        return self

    def add(self, src: str, dst: str, *, chown: str | None = None) -> "DockerfileBuilder":
        self._current_directives.append(Add(src=src, dst=dst, chown=chown))
        return self

    def workdir(self, path: str) -> "DockerfileBuilder":
        self._current_directives.append(Workdir(path=path))
        return self

    def user(self, user: str, group: str | None = None) -> "DockerfileBuilder":
        self._current_directives.append(User(user=user, group=group))
        return self

    def expose(self, port: int, protocol: str | None = None) -> "DockerfileBuilder":
        self._current_directives.append(Expose(port=port, protocol=protocol))
        return self

    def entrypoint(self, *args: str) -> "DockerfileBuilder":
        self._current_directives.append(Entrypoint(args=args))
        return self

    def cmd(self, *args: str) -> "DockerfileBuilder":
        self._current_directives.append(Cmd(args=args))
        return self

    def arg(self, name: str, default: str | None = None) -> "DockerfileBuilder":
        self._current_directives.append(Arg(name=name, default=default))
        return self

    def env(self, key: str, value: str) -> "DockerfileBuilder":
        self._current_directives.append(Env(key=key, value=value))
        return self

    def label(self, labels: dict[str, str]) -> "DockerfileBuilder":
        self._current_directives.append(Label(labels=labels))
        return self

    def volume(self, *paths: str) -> "DockerfileBuilder":
        self._current_directives.append(Volume(paths=paths))
        return self

    def shell(self, *args: str) -> "DockerfileBuilder":
        self._current_directives.append(Shell(args=args))
        return self

    def healthcheck(
        self,
        command: str,
        *,
        interval_seconds: int = 10,
        timeout_seconds: int = 5,
        start_period_seconds: int = 30,
        retries: int = 3,
    ) -> "DockerfileBuilder":
        self._current_directives.append(HealthCheck(
            command=command,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            start_period_seconds=start_period_seconds,
            retries=retries,
        ))
        return self

    def healthcheck_none(self) -> "DockerfileBuilder":
        self._current_directives.append(HealthCheckNone())
        return self

    def comment(self, text: str) -> "DockerfileBuilder":
        self._current_directives.append(Comment(text=text))
        return self

    def blank(self) -> "DockerfileBuilder":
        self._current_directives.append(BlankLine())
        return self

    def directive(self, d: Directive) -> "DockerfileBuilder":
        """Add a pre-built directive directly."""
        self._current_directives.append(d)
        return self

    def build(self) -> Dockerfile:
        """Finalize and return the Dockerfile."""
        self._flush_stage()
        if not self._stages:
            raise ValueError("Dockerfile must have at least one FROM stage")
        return Dockerfile(stages=tuple(self._stages))
