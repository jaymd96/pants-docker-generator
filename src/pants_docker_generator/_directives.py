"""Dockerfile instruction dataclasses.

Each class represents a single Dockerfile instruction and can render itself
to its string representation via ``render()``.
"""

from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass(frozen=True)
class Comment:
    """A Dockerfile comment line."""

    text: str

    def render(self) -> str:
        return f"# {self.text}"


@dataclass(frozen=True)
class BlankLine:
    """An empty line for readability."""

    def render(self) -> str:
        return ""


@dataclass(frozen=True)
class From:
    """FROM instruction."""

    image: str
    alias: Optional[str] = None
    platform: Optional[str] = None

    def render(self) -> str:
        parts = ["FROM"]
        if self.platform:
            parts.append(f"--platform={self.platform}")
        parts.append(self.image)
        if self.alias:
            parts.append(f"AS {self.alias}")
        return " ".join(parts)


@dataclass(frozen=True)
class Run:
    """RUN instruction."""

    command: str

    def render(self) -> str:
        return f"RUN {self.command}"


@dataclass(frozen=True)
class Copy:
    """COPY instruction."""

    src: str
    dst: str
    from_stage: Optional[str] = None
    chown: Optional[str] = None

    def render(self) -> str:
        parts = ["COPY"]
        if self.from_stage:
            parts.append(f"--from={self.from_stage}")
        if self.chown:
            parts.append(f"--chown={self.chown}")
        parts.append(self.src)
        parts.append(self.dst)
        return " ".join(parts)


@dataclass(frozen=True)
class Add:
    """ADD instruction."""

    src: str
    dst: str
    chown: Optional[str] = None

    def render(self) -> str:
        parts = ["ADD"]
        if self.chown:
            parts.append(f"--chown={self.chown}")
        parts.append(self.src)
        parts.append(self.dst)
        return " ".join(parts)


@dataclass(frozen=True)
class Workdir:
    """WORKDIR instruction."""

    path: str

    def render(self) -> str:
        return f"WORKDIR {self.path}"


@dataclass(frozen=True)
class User:
    """USER instruction."""

    user: str
    group: Optional[str] = None

    def render(self) -> str:
        if self.group:
            return f"USER {self.user}:{self.group}"
        return f"USER {self.user}"


@dataclass(frozen=True)
class Expose:
    """EXPOSE instruction."""

    port: int
    protocol: Optional[str] = None

    def render(self) -> str:
        if self.protocol:
            return f"EXPOSE {self.port}/{self.protocol}"
        return f"EXPOSE {self.port}"


@dataclass(frozen=True)
class Entrypoint:
    """ENTRYPOINT instruction (exec form)."""

    args: tuple[str, ...]

    def render(self) -> str:
        parts = ", ".join(f'"{a}"' for a in self.args)
        return f"ENTRYPOINT [{parts}]"


@dataclass(frozen=True)
class Cmd:
    """CMD instruction (exec form)."""

    args: tuple[str, ...]

    def render(self) -> str:
        parts = ", ".join(f'"{a}"' for a in self.args)
        return f"CMD [{parts}]"


@dataclass(frozen=True)
class Arg:
    """ARG instruction."""

    name: str
    default: Optional[str] = None

    def render(self) -> str:
        if self.default is not None:
            return f"ARG {self.name}={self.default}"
        return f"ARG {self.name}"


@dataclass(frozen=True)
class Env:
    """ENV instruction."""

    key: str
    value: str

    def render(self) -> str:
        return f'ENV {self.key}="{self.value}"'


@dataclass(frozen=True)
class Label:
    """LABEL instruction with one or more key-value pairs."""

    labels: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        if not self.labels:
            return ""
        if len(self.labels) == 1:
            k, v = next(iter(self.labels.items()))
            return f'LABEL {k}="{v}"'
        lines = ["LABEL \\"]
        items = list(self.labels.items())
        for i, (k, v) in enumerate(items):
            suffix = " \\" if i < len(items) - 1 else ""
            lines.append(f'      {k}="{v}"{suffix}')
        return "\n".join(lines)


@dataclass(frozen=True)
class Volume:
    """VOLUME instruction."""

    paths: tuple[str, ...]

    def render(self) -> str:
        if len(self.paths) == 1:
            return f"VOLUME {self.paths[0]}"
        parts = ", ".join(f'"{p}"' for p in self.paths)
        return f"VOLUME [{parts}]"


@dataclass(frozen=True)
class Shell:
    """SHELL instruction."""

    args: tuple[str, ...]

    def render(self) -> str:
        parts = ", ".join(f'"{a}"' for a in self.args)
        return f"SHELL [{parts}]"


@dataclass(frozen=True)
class HealthCheck:
    """HEALTHCHECK instruction."""

    command: str
    interval_seconds: int = 10
    timeout_seconds: int = 5
    start_period_seconds: int = 30
    retries: int = 3

    def render(self) -> str:
        return (
            f"HEALTHCHECK --interval={self.interval_seconds}s "
            f"--timeout={self.timeout_seconds}s "
            f"--start-period={self.start_period_seconds}s "
            f"--retries={self.retries} \\\n"
            f"  CMD {self.command}"
        )


@dataclass(frozen=True)
class HealthCheckNone:
    """HEALTHCHECK NONE - disables health check inherited from base image."""

    def render(self) -> str:
        return "HEALTHCHECK NONE"


# Union type for all directives
Directive = Union[
    Comment, BlankLine, From, Run, Copy, Add, Workdir, User,
    Expose, Entrypoint, Cmd, Arg, Env, Label, Volume, Shell,
    HealthCheck, HealthCheckNone,
]
