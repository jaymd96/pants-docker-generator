---
description: Generate Dockerfiles programmatically using directives, builder pattern, and presets
user_invocable: true
triggers:
  - "docker"
  - "dockerfile"
  - "docker generator"
  - "dockerignore"
  - "oci labels"
  - "sls dockerfile"
  - "docker builder"
---

# Docker Generator

You are an expert on the `pants-docker-generator` library (v0.2.0). Use this knowledge to help developers generate Dockerfiles programmatically.

## Overview

Three levels of abstraction, from low to high:

1. **Directives** -- individual Dockerfile instructions as frozen dataclasses (`From`, `Run`, `Copy`, etc.)
2. **DockerfileBuilder** -- fluent builder that assembles directives into multi-stage `Dockerfile` objects
3. **Presets** -- one-call functions for common patterns (`sls_dockerfile`, `sls_dockerignore`)

All types are immutable (frozen dataclasses). The library has zero external dependencies.

```python
from pants_docker_generator import DockerfileBuilder

df = (DockerfileBuilder()
    .from_("python:3.11-slim")
    .workdir("/app")
    .copy("requirements.txt", ".")
    .run("pip install --no-cache-dir -r requirements.txt")
    .copy(".", ".")
    .expose(8080)
    .cmd("python", "app.py")
    .build())

print(df.render())
```

## Directive-Level Usage

Every Dockerfile instruction is a frozen dataclass with a `render()` method:

```python
from pants_docker_generator import From, Run, Copy, Env, Expose

# Create directives directly
f = From(image="python:3.11-slim", alias="builder", platform="linux/amd64")
r = Run(command="pip install --no-cache-dir -r requirements.txt")
c = Copy(src="app.py", dst="/app/", from_stage="builder", chown="1000:1000")
e = Env(key="PYTHONDONTWRITEBYTECODE", value="1")
p = Expose(port=8080, protocol="tcp")

# Render to strings
print(f.render())  # FROM --platform=linux/amd64 python:3.11-slim AS builder
print(r.render())  # RUN pip install --no-cache-dir -r requirements.txt
print(c.render())  # COPY --from=builder --chown=1000:1000 app.py /app/
print(e.render())  # ENV PYTHONDONTWRITEBYTECODE="1"
print(p.render())  # EXPOSE 8080/tcp
```

For the full directive API, see [reference/directives-api.md](reference/directives-api.md).

## Builder API

`DockerfileBuilder` provides a fluent interface. Every method returns `self` for chaining. Call `.build()` at the end to get an immutable `Dockerfile`.

```python
from pants_docker_generator import DockerfileBuilder

df = (DockerfileBuilder()
    .from_("python:3.11-slim")
    .arg("APP_VERSION", "1.0.0")
    .env("APP_VERSION", "${APP_VERSION}")
    .workdir("/app")
    .copy("requirements.txt", ".")
    .run("pip install --no-cache-dir -r requirements.txt")
    .copy(".", ".")
    .user("1000", "1000")
    .expose(8080)
    .healthcheck("curl -f http://localhost:8080/health || exit 1",
                 interval_seconds=30, timeout_seconds=5)
    .entrypoint("python", "-m", "myapp")
    .cmd("--port", "8080")
    .build())
```

Builder methods: `from_`, `run`, `copy`, `add`, `workdir`, `user`, `expose`, `entrypoint`, `cmd`, `arg`, `env`, `label`, `volume`, `shell`, `healthcheck`, `healthcheck_none`, `comment`, `blank`, `directive`, `build`.

For full signatures see [reference/builder-api.md](reference/builder-api.md).

## Multi-Stage Builds

Each `from_()` call starts a new stage. Use `alias` to name stages and `from_stage` on `copy` to reference them:

```python
df = (DockerfileBuilder()
    # Build stage
    .from_("python:3.11-slim", alias="builder")
    .workdir("/build")
    .copy(".", ".")
    .run("pip install --no-cache-dir -r requirements.txt")
    .run("python setup.py bdist_wheel")
    .blank()
    # Runtime stage
    .from_("python:3.11-slim", alias="runtime")
    .workdir("/app")
    .copy("--from=builder", "/build/dist/*.whl", "/tmp/")
    .run("pip install /tmp/*.whl && rm /tmp/*.whl")
    .user("1000")
    .entrypoint("python", "-m", "myapp")
    .build())

# Dockerfile.stages is a tuple of Stage objects
assert len(df.stages) == 2
assert df.stages[0].alias == "builder"
assert df.stages[1].alias == "runtime"
```

## OCI Labels

The `oci_labels()` helper generates a `Label` directive with standard OCI annotation keys:

```python
from pants_docker_generator import oci_labels

lbl = oci_labels(
    title="my-service",
    version="1.0.0",
    vendor="com.example",
    description="My service",
    source="https://github.com/example/my-service",
    licenses="Apache-2.0",
    extra={"com.example.team": "platform"},
)
# Returns a Label directive with org.opencontainers.image.* keys
```

Standard OCI keys: `title`, `version`, `vendor`, `description`, `url`, `source`, `licenses`, `revision`, `created`. Only non-None values are included. `extra` is merged last.

## Dockerignore Generation

```python
from pants_docker_generator import generate_dockerignore, DockerignoreConfig

# Simple: ignore everything except specific patterns
content = generate_dockerignore(
    allow=("*.whl", "requirements.txt"),
    comment="Only include wheels and requirements",
)
# Output:
# # Only include wheels and requirements
# **
# !*.whl
# !requirements.txt

# Advanced: use DockerignoreConfig for full control
config = DockerignoreConfig(
    ignore_all=True,
    allow_patterns=("*.sls.tgz", "hooks/"),
    deny_patterns=("*.pyc",),
    comment="SLS build context",
)
content = config.render()
```

## SLS Preset

The `sls_dockerfile()` function generates a complete Dockerfile for SLS distributions. This is consumed by the `pants-sls-distribution` plugin.

```python
from pants_docker_generator import sls_dockerfile, sls_dockerignore

df = sls_dockerfile(
    base_image="python:3.11-slim",
    product_name="my-service",
    product_version="1.0.0",
    product_group="com.example",
    dist_name="my-service-1.0.0",
    tarball_name="my-service-1.0.0.sls.tgz",
    install_path="/opt/services",         # default
    product_type="helm.v1",               # default
    use_hook_init=True,                   # enables hook init system
    expose_ports=(8080, 8081),
    health_check_interval=30,
    health_check_timeout=5,
    labels={"com.example.team": "platform"},
)

ignore = sls_dockerignore()
# Allows only *.sls.tgz and hooks/
```

For full parameter reference see [reference/presets-api.md](reference/presets-api.md).

## Dev & Testing

```bash
hatch run test          # Run test suite
hatch run lint          # Check code quality (Ruff)
hatch run fmt           # Format code (Ruff)
hatch build             # Build wheel
```

## Bundling with pants-claude-plugins

This skill is automatically delivered to projects using `pants-sls-distribution`, which bundles it via `bundled_claude_plugins.py`. No extra setup needed -- run `pants claude-install --include-bundled ::`.

For standalone use outside SLS, declare the plugin in a BUILD file:

```python
claude_plugin(
    name="docker-generator",
    plugin="docker-generator",
    marketplace="docker-generator",
    scope="project",
)
```

## Gotchas

- All directives are **frozen dataclasses** -- you cannot mutate them after creation.
- `DockerfileBuilder` is mutable (it accumulates directives), but `.build()` returns an immutable `Dockerfile`.
- The builder **must start with `from_()`** -- calling any other method first will add directives to a stage with no FROM, and `.build()` will raise `ValueError`.
- `.build()` flushes the last stage -- don't forget to call it.
- `Label.labels` is a plain `dict` on the frozen dataclass. This works because Label uses `field(default_factory=dict)`.
- `Entrypoint` and `Cmd` use exec form (JSON array), not shell form. Pass multiple string args.
- `Copy.from_stage` uses the `--from=` flag syntax, matching Docker's COPY instruction.
