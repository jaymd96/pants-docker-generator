"""Dockerignore file generation."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class DockerignoreConfig:
    """Configuration for .dockerignore generation."""

    ignore_all: bool = True
    allow_patterns: tuple[str, ...] = ()
    deny_patterns: tuple[str, ...] = ()
    comment: Optional[str] = None

    def render(self) -> str:
        lines: list[str] = []
        if self.comment:
            lines.append(f"# {self.comment}")
        for pattern in self.deny_patterns:
            lines.append(pattern)
        if self.ignore_all:
            lines.append("**")
        for pattern in self.allow_patterns:
            lines.append(f"!{pattern}")
        lines.append("")  # trailing newline
        return "\n".join(lines)


def generate_dockerignore(
    *,
    allow: tuple[str, ...] = (),
    comment: Optional[str] = None,
) -> str:
    """Generate a .dockerignore that blocks everything except ``allow`` patterns."""
    config = DockerignoreConfig(
        ignore_all=True,
        allow_patterns=allow,
        comment=comment,
    )
    return config.render()
