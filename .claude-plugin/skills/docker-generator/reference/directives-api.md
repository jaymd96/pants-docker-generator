# Directives API Reference

All directives are frozen dataclasses in `pants_docker_generator._directives`. Each has a `render() -> str` method.

The union type `Directive` encompasses all directive types.

## Comment

```python
@dataclass(frozen=True)
class Comment:
    text: str
    # render() -> "# {text}"
```

## BlankLine

```python
@dataclass(frozen=True)
class BlankLine:
    # render() -> ""
```

## From

```python
@dataclass(frozen=True)
class From:
    image: str
    alias: Optional[str] = None       # AS {alias}
    platform: Optional[str] = None    # --platform={platform}
    # render() -> "FROM [--platform=P] image [AS alias]"
```

## Run

```python
@dataclass(frozen=True)
class Run:
    command: str
    # render() -> "RUN {command}"
```

## Copy

```python
@dataclass(frozen=True)
class Copy:
    src: str
    dst: str
    from_stage: Optional[str] = None  # --from={from_stage}
    chown: Optional[str] = None       # --chown={chown}
    # render() -> "COPY [--from=S] [--chown=O] src dst"
```

## Add

```python
@dataclass(frozen=True)
class Add:
    src: str
    dst: str
    chown: Optional[str] = None       # --chown={chown}
    # render() -> "ADD [--chown=O] src dst"
```

## Workdir

```python
@dataclass(frozen=True)
class Workdir:
    path: str
    # render() -> "WORKDIR {path}"
```

## User

```python
@dataclass(frozen=True)
class User:
    user: str
    group: Optional[str] = None
    # render() -> "USER user[:group]"
```

## Expose

```python
@dataclass(frozen=True)
class Expose:
    port: int
    protocol: Optional[str] = None    # e.g., "tcp", "udp"
    # render() -> "EXPOSE port[/protocol]"
```

## Entrypoint

```python
@dataclass(frozen=True)
class Entrypoint:
    args: tuple[str, ...]
    # render() -> 'ENTRYPOINT ["arg1", "arg2", ...]'  (exec form)
```

## Cmd

```python
@dataclass(frozen=True)
class Cmd:
    args: tuple[str, ...]
    # render() -> 'CMD ["arg1", "arg2", ...]'  (exec form)
```

## Arg

```python
@dataclass(frozen=True)
class Arg:
    name: str
    default: Optional[str] = None
    # render() -> "ARG name[=default]"
```

## Env

```python
@dataclass(frozen=True)
class Env:
    key: str
    value: str
    # render() -> 'ENV key="value"'
```

## Label

```python
@dataclass(frozen=True)
class Label:
    labels: dict[str, str] = field(default_factory=dict)
    # Single label:  'LABEL key="value"'
    # Multiple:      'LABEL \\\n      k1="v1" \\\n      k2="v2"'
```

## Volume

```python
@dataclass(frozen=True)
class Volume:
    paths: tuple[str, ...]
    # Single path:   "VOLUME /data"
    # Multiple:      'VOLUME ["/data", "/logs"]'
```

## Shell

```python
@dataclass(frozen=True)
class Shell:
    args: tuple[str, ...]
    # render() -> 'SHELL ["arg1", "arg2"]'
```

## HealthCheck

```python
@dataclass(frozen=True)
class HealthCheck:
    command: str
    interval_seconds: int = 10
    timeout_seconds: int = 5
    start_period_seconds: int = 30
    retries: int = 3
    # render() -> "HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \\\n  CMD {command}"
```

## HealthCheckNone

```python
@dataclass(frozen=True)
class HealthCheckNone:
    # render() -> "HEALTHCHECK NONE"
```

## Directive Union Type

```python
Directive = Union[
    Comment, BlankLine, From, Run, Copy, Add, Workdir, User,
    Expose, Entrypoint, Cmd, Arg, Env, Label, Volume, Shell,
    HealthCheck, HealthCheckNone,
]
```
