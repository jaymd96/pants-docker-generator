# Builder API Reference

## DockerfileBuilder

Mutable fluent builder. Every method returns `self` for chaining. Call `.build()` to finalize.

```python
class DockerfileBuilder:
    def __init__(self) -> None: ...
```

### Stage Management

```python
def from_(self, image: str, *, alias: Optional[str] = None, platform: Optional[str] = None) -> DockerfileBuilder
```
Start a new stage. If a previous stage is in progress, it is flushed. Must be called before any other directive method.

```python
def build(self) -> Dockerfile
```
Finalize and return an immutable `Dockerfile`. Flushes the last stage. Raises `ValueError` if no stages were created.

### Instruction Methods

All return `DockerfileBuilder` for chaining.

```python
def run(self, command: str) -> DockerfileBuilder
def copy(self, src: str, dst: str, *, from_stage: Optional[str] = None, chown: Optional[str] = None) -> DockerfileBuilder
def add(self, src: str, dst: str, *, chown: Optional[str] = None) -> DockerfileBuilder
def workdir(self, path: str) -> DockerfileBuilder
def user(self, user: str, group: Optional[str] = None) -> DockerfileBuilder
def expose(self, port: int, protocol: Optional[str] = None) -> DockerfileBuilder
def entrypoint(self, *args: str) -> DockerfileBuilder
def cmd(self, *args: str) -> DockerfileBuilder
def arg(self, name: str, default: Optional[str] = None) -> DockerfileBuilder
def env(self, key: str, value: str) -> DockerfileBuilder
def label(self, labels: Dict[str, str]) -> DockerfileBuilder
def volume(self, *paths: str) -> DockerfileBuilder
def shell(self, *args: str) -> DockerfileBuilder
```

### Health Check Methods

```python
def healthcheck(
    self,
    command: str,
    *,
    interval_seconds: int = 10,
    timeout_seconds: int = 5,
    start_period_seconds: int = 30,
    retries: int = 3,
) -> DockerfileBuilder

def healthcheck_none(self) -> DockerfileBuilder
```

### Formatting Methods

```python
def comment(self, text: str) -> DockerfileBuilder    # "# {text}"
def blank(self) -> DockerfileBuilder                  # empty line
```

### Raw Directive Injection

```python
def directive(self, d: Directive) -> DockerfileBuilder
```
Add a pre-built directive object directly to the current stage.

## Stage

Immutable representation of a single Dockerfile stage.

```python
@dataclass(frozen=True)
class Stage:
    from_directive: From
    directives: tuple[Directive, ...] = ()

    @property
    def alias(self) -> Optional[str]    # Shortcut for from_directive.alias

    def render(self) -> str             # Renders FROM + all directives
```

## Dockerfile

Immutable representation of a complete Dockerfile.

```python
@dataclass(frozen=True)
class Dockerfile:
    stages: tuple[Stage, ...]

    def render(self) -> str             # Full Dockerfile text (newline-terminated)
    def __str__(self) -> str            # Same as render()
```

Stages are separated by blank lines in rendered output.
