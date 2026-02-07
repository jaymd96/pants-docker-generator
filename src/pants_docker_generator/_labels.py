"""OCI image label helpers."""

from typing import Dict, Optional

from pants_docker_generator._directives import Label


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
) -> Label:
    """Build a Label directive with standard OCI annotation keys.

    Only non-None values are included. ``extra`` is merged last.
    """
    labels: dict[str, str] = {}
    mapping = {
        "org.opencontainers.image.title": title,
        "org.opencontainers.image.version": version,
        "org.opencontainers.image.vendor": vendor,
        "org.opencontainers.image.description": description,
        "org.opencontainers.image.url": url,
        "org.opencontainers.image.source": source,
        "org.opencontainers.image.licenses": licenses,
        "org.opencontainers.image.revision": revision,
        "org.opencontainers.image.created": created,
    }
    for key, value in mapping.items():
        if value is not None:
            labels[key] = value
    if extra:
        labels.update(extra)
    return Label(labels=labels)
