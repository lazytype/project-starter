import dataclasses
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from string.templatelib import Template
from typing import Self, final

ADDITIONAL_EXTENSIONS_BY_FORMAT_EXTENSION: Mapping[str, Sequence[str]] = {
  "tar.bz2": [],
  "tar.gz": ["tgz"],
  "tar.xz": [],
  "tar.zst": [],
  "tar": [],
  "zip": [],
  "bz2": [],
  "gz": [],
  "xz": [],
  "zst": [],
}


def _iter_extension_format_tuples() -> Iterator[tuple[str, str]]:
  for key, values in ADDITIONAL_EXTENSIONS_BY_FORMAT_EXTENSION.items():
    yield (key, key)
    yield from ((value, key) for value in values)


@final
class DotslashVersion:
  def __init__(self, major: int, minor: int, patch: int):
    self._major = major
    self._minor = minor
    self._patch = patch

  def id(self) -> Self:
    return self

  def __str__(self) -> str:
    return f"{self._major}.{self._minor}.{self._patch}"

  def major(self) -> int:
    return self._major


@dataclass
class DotslashPlatform:
  name: str
  path_template: Template
  provider_url_template: Template


@final
class DotslashBinary:
  def __init__(
    self, *, name: str, version: DotslashVersion, platforms: Sequence[DotslashPlatform]
  ):
    self.name = name
    self.version = version
    self.platforms = [
      DotslashPlatformInternal(version=self.version, platform=platform)
      for platform in platforms
    ]

  @property
  def _dotslash_name(self) -> str:
    return f"{self.name}-v{self.version}"

  def json(self) -> dict[str, object]:
    return {
      "name": self._dotslash_name,
      "platforms": {platform.name: platform.json() for platform in self.platforms},
    }


@final
class DotslashPlatformInternal(DotslashPlatform):
  def __init__(self, *, version: DotslashVersion, platform: DotslashPlatform):
    super().__init__(**dataclasses.asdict(platform))
    self.version = version

  @property
  def _format(self) -> str | None:
    for extension, format in sorted(
      _iter_extension_format_tuples(),
      key=lambda extension_format_tuple: len(extension_format_tuple[0]),
      reverse=True,
    ):
      if self._provider_url.endswith(f".{extension}"):
        return format
    return None

  def _render_template(self, template: Template) -> str:
    parts: list[str] = []
    for item in template:
      if isinstance(item, str):
        parts.append(item)
      else:
        parts.append(str(item.value(self.version)))

    return "".join(parts)

  @property
  def _path(self) -> str:
    return self._render_template(self.path_template)

  @property
  def _provider_url(self) -> str:
    return self._render_template(self.provider_url_template)

  def json(self) -> dict[str, object]:
    import hashlib
    import urllib.request

    with urllib.request.urlopen(self._provider_url) as response:
      data = response.read()

    result: dict[str, object] = {
      "size": len(data),
      "hash": "sha256",
      "digest": hashlib.sha256(data).hexdigest(),
      "format": self._format,
      "path": self._path,
      "providers": [{"url": self._provider_url}],
    }

    if result["format"] is None:
      del result["format"]

    return result


binary = DotslashBinary
platform = DotslashPlatform
version = DotslashVersion


__all__ = ["binary", "platform", "version"]
