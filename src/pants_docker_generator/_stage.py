"""Multi-stage build support."""

from dataclasses import dataclass, field

from pants_docker_generator._directives import Directive, From


@dataclass(frozen=True)
class Stage:
    """A single stage in a multi-stage Dockerfile."""

    from_directive: From
    directives: tuple[Directive, ...] = ()

    @property
    def alias(self) -> str | None:
        return self.from_directive.alias

    def render(self) -> str:
        lines = [self.from_directive.render()]
        for d in self.directives:
            rendered = d.render()
            if rendered is not None:
                lines.append(rendered)
        return "\n".join(lines)
