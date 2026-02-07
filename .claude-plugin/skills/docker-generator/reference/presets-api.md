# Presets API Reference

## sls_dockerfile

Generates a complete Dockerfile for an SLS distribution. This is the highest-level API, consumed by `pants-sls-distribution`.

```python
def sls_dockerfile(
    *,
    base_image: str,                              # Required: base Docker image
    product_name: str,                            # Required: SLS product name
    product_version: str,                         # Required: SLS product version
    product_group: str,                           # Required: SLS product group
    dist_name: str,                               # Required: distribution name (used for paths)
    tarball_name: str,                            # Required: tarball filename (e.g., "my-service-1.0.0.sls.tgz")
    install_path: str = "/opt/services",          # Container install path
    product_type: str = "helm.v1",                # SLS product type label
    health_check_interval: Optional[int] = None,  # Seconds between health checks
    health_check_timeout: Optional[int] = None,   # Seconds before health check timeout
    health_check_start_period: Optional[int] = None,  # Grace period before first check
    health_check_retries: Optional[int] = None,   # Retries before marking unhealthy
    use_hook_init: bool = False,                  # Enable hook init system
    expose_ports: tuple[int, ...] = (),           # Ports to EXPOSE
    labels: Optional[Dict[str, str]] = None,      # Additional labels (merged with OCI defaults)
) -> Dockerfile
```

### Generated Layout

The returned Dockerfile contains:

1. `FROM base_image`
2. `LABEL` with OCI annotations (title, version, vendor, product-type) + custom labels
3. `ADD tarball_name install_path/` -- extracts the SLS tarball
4. `WORKDIR install_path/dist_name`
5. `RUN mkdir -p var/data/tmp var/log var/run var/conf var/state`
6. (If `use_hook_init`) Hook init system: COPY entrypoint.sh, hooks.sh; RUN chmod + mkdir hook dirs
7. (If `expose_ports`) EXPOSE for each port
8. (If health check params set) HEALTHCHECK with `service/monitoring/bin/check.sh`
9. ENTRYPOINT: `service/bin/entrypoint.sh` (with hooks) or `service/bin/init.sh start` (without)

### Default Labels

Always included:
- `org.opencontainers.image.title` = product_name
- `org.opencontainers.image.version` = product_version
- `org.opencontainers.image.vendor` = product_group
- `com.palantir.sls.product-type` = product_type

## sls_dockerignore

Generates a `.dockerignore` that allows only SLS build context files.

```python
def sls_dockerignore() -> str
```

Output:
```
# Ignore everything except the tarball and hook files
**
!*.sls.tgz
!hooks/
```

## oci_labels

Helper to build a `Label` directive with standard OCI annotation keys.

```python
def oci_labels(
    *,
    title: Optional[str] = None,
    version: Optional[str] = None,
    vendor: Optional[str] = None,
    description: Optional[str] = None,
    url: Optional[str] = None,
    source: Optional[str] = None,
    licenses: Optional[str] = None,
    revision: Optional[str] = None,
    created: Optional[str] = None,
    extra: Optional[Dict[str, str]] = None,
) -> Label
```

Maps each parameter to `org.opencontainers.image.*` keys. Only non-None values are included. `extra` is merged last (can add or override any key).

## DockerignoreConfig

Low-level dataclass for custom `.dockerignore` generation.

```python
@dataclass(frozen=True)
class DockerignoreConfig:
    ignore_all: bool = True                    # If True, starts with "**" (deny all)
    allow_patterns: tuple[str, ...] = ()       # Prefixed with "!" in output
    deny_patterns: tuple[str, ...] = ()        # Added before the "**" line
    comment: Optional[str] = None              # Comment at top of file

    def render(self) -> str
```

## generate_dockerignore

Convenience function wrapping `DockerignoreConfig`.

```python
def generate_dockerignore(
    *,
    allow: tuple[str, ...] = (),
    comment: Optional[str] = None,
) -> str
```

Creates a config with `ignore_all=True` and the given allow patterns.
