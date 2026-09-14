"""
Copy the architecture and package documentation out of the server repo into this site.

The server repo is the single source of truth for both trees. Its documents link to each other
with ordinary relative paths, which work on GitHub and in an editor but not once the files are
copied to different depths here, so every link is rewritten: to a site path when the target was
also copied, and to a GitHub URL when it is source code that was not.

Usage:
    python scripts/pull_server_docs.py <server-checkout> [--output docs]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# ruff: noqa: T201

BLOB_BASE = "https://github.com/music-assistant/server/blob/dev"

ARCHITECTURE_SRC = Path("docs/architecture")
PACKAGE_SRC = Path("music_assistant")
ARCHITECTURE_DEST = Path("architecture")
PACKAGE_DEST = Path("packages")

INLINE_LINK = re.compile(r"(!?\[[^\]]*\]\()\s*<?([^)\s>]+)>?(\s*(?:\"[^\"]*\")?\s*\))")
CODE_FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)")
EXTERNAL = ("http://", "https://", "mailto:", "tel:", "data:", "//", "#")

LOCAL_MD_LINK = re.compile(r"\]\(([A-Za-z0-9._-]+\.md)(?:#[^)]*)?\)")


def main(argv: list[str] | None = None) -> int:
    """Copy the server's documentation into this site and rewrite its links."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("server", type=Path, help="path to a music-assistant/server checkout")
    parser.add_argument("--output", type=Path, default=Path("docs"), help="site docs directory")
    args = parser.parse_args(argv)

    server: Path = args.server.resolve()
    output: Path = args.output.resolve()
    if not (server / ARCHITECTURE_SRC).is_dir():
        print(f"error: {server} does not look like a server checkout", file=sys.stderr)
        return 1

    mapping = _build_mapping(server)
    for dest in (ARCHITECTURE_DEST, PACKAGE_DEST):
        shutil.rmtree(output / dest, ignore_errors=True)

    for repo_path, site_path in sorted(mapping.items()):
        source = server / repo_path
        target = output / site_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_rewrite_links(source.read_text("utf-8"), repo_path, site_path, mapping))

    _write_nav_files(output)
    print(f"copied {len(mapping)} documents into {output}")
    return 0


def _build_mapping(server: Path) -> dict[str, str]:
    """
    Return ``{repo-relative source: site-relative destination}`` for every document to copy.

    A ``README.md`` becomes ``index.md`` so its directory gets a landing page in the nav.
    """
    mapping: dict[str, str] = {}
    for source, dest_root in ((ARCHITECTURE_SRC, ARCHITECTURE_DEST), (PACKAGE_SRC, PACKAGE_DEST)):
        for path in sorted((server / source).rglob("*.md")):
            relative = path.relative_to(server / source)
            name = "index.md" if path.name == "README.md" else path.name
            mapping[path.relative_to(server).as_posix()] = (
                dest_root / relative.parent / name
            ).as_posix()
    return mapping


def _rewrite_links(text: str, repo_path: str, site_path: str, mapping: dict[str, str]) -> str:
    """
    Return the document with every relative link repointed for its new location.

    :param text: The document's markdown.
    :param repo_path: Where it came from, so relative targets resolve the way the author meant.
    :param site_path: Where it is going, so site-relative links are computed from the right place.
    :param mapping: Every source-to-destination pair in this copy.
    """
    out: list[str] = []
    in_fence = False
    for raw_line in text.splitlines():
        if CODE_FENCE.match(raw_line):
            in_fence = not in_fence
            out.append(raw_line)
            continue
        if in_fence or "](" not in raw_line:
            out.append(raw_line)
            continue
        out.append(_rewrite_line(raw_line, repo_path, site_path, mapping))
    return "\n".join(out) + "\n"


def _rewrite_line(line: str, repo_path: str, site_path: str, mapping: dict[str, str]) -> str:
    """Rewrite every link on one line, leaving links inside inline code untouched."""
    protected = {m.span() for m in INLINE_CODE.finditer(line)}

    def replace(match: re.Match[str]) -> str:
        if any(start <= match.start() < end for start, end in protected):
            return match.group(0)
        target = match.group(2)
        if target.startswith(EXTERNAL):
            return match.group(0)
        path_part, _, anchor = target.partition("#")
        anchor = f"#{anchor}" if anchor else ""
        resolved = _resolve(repo_path, path_part, mapping)
        if resolved is None:
            return match.group(0)
        return f"{match.group(1)}{resolved}{anchor}{match.group(3)}"

    return INLINE_LINK.sub(replace, line)


def _resolve(repo_path: str, path_part: str, mapping: dict[str, str]) -> str | None:
    """Return the rewritten target for one link, or ``None`` to leave it alone."""
    if not path_part:
        return None
    repo_target = _normalize(Path(repo_path).parent / path_part)
    if repo_target in mapping:
        return _relative(mapping[repo_path], mapping[repo_target])
    readme = f"{repo_target}/README.md"
    if readme in mapping:
        return _relative(mapping[repo_path], mapping[readme])
    return f"{BLOB_BASE}/{repo_target}"


def _normalize(path: Path) -> str:
    """Collapse ``..`` segments without touching the filesystem, since nothing here exists yet."""
    parts: list[str] = []
    for part in path.as_posix().split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def _relative(from_site_path: str, to_site_path: str) -> str:
    """Return a link from one copied page to another."""
    import posixpath

    return posixpath.relpath(to_site_path, posixpath.dirname(from_site_path))


def _architecture_order(architecture: Path) -> list[str]:
    """
    Return the architecture pages in the order its index links to them.

    The index is what tells a human which order to read these in, so it decides the nav order
    too rather than this script keeping a second list that would drift away from it.

    :param architecture: The copied architecture directory.
    """
    index = architecture / "index.md"
    if not index.is_file():
        return []
    present = {path.name for path in architecture.glob("*.md")}
    ordered = ["index.md"]
    for name in LOCAL_MD_LINK.findall(index.read_text("utf-8")):
        if name in present and name not in ordered:
            ordered.append(name)
    return ordered


def _write_packages_index(packages: Path) -> None:
    """
    Write a landing page listing every copied package, grouped by kind.

    The packages tree has no counterpart in the server repo, so unlike every other page here this
    one is generated rather than copied.

    :param packages: The copied packages directory.
    """
    lines = [
        "# Package docs",
        "",
        "Documentation living beside the code it describes, copied from the",
        "[server repository](https://github.com/music-assistant/server). Start from the",
        "[architecture](../architecture/index.md) pages for the big picture; these hold the detail.",
    ]
    for group, heading in (("controllers", "Controllers"), ("providers", "Providers")):
        group_dir = packages / group
        if not group_dir.is_dir():
            continue
        lines += ["", f"## {heading}", ""]
        for index in sorted(group_dir.rglob("index.md")):
            name = index.parent.relative_to(group_dir).as_posix()
            lines.append(f"- [{name}]({group}/{name}/index.md): {_title_of(index)}")
    (packages / "index.md").write_text("\n".join(lines) + "\n")


def _title_of(index: Path) -> str:
    """Return a page's first heading, for use as a link description."""
    for line in index.read_text("utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _write_nav_files(output: Path) -> None:
    """Write the nav files that give the copied trees a sensible order and titles."""
    architecture = output / ARCHITECTURE_DEST
    if architecture.is_dir():
        ordered = _architecture_order(architecture)
        entries = "\n".join(f"  - {name}" for name in ordered)
        # a trailing glob catches any page the index does not link to yet
        unlinked = {path.name for path in architecture.glob("*.md")} - set(ordered)
        glob = "\n  - '*'" if unlinked else ""
        (architecture / ".nav.yml").write_text(f"title: Architecture\nnav:\n{entries}{glob}\n")

    packages = output / PACKAGE_DEST
    if packages.is_dir():
        _write_packages_index(packages)
        (packages / ".nav.yml").write_text(
            "title: Package docs\nuse_index_title: true\nsort:\n  by: filename\n"
        )
        for child in sorted(packages.rglob("*")):
            if not child.is_dir() or not (child / "index.md").exists():
                continue
            # only add the glob where there is something besides the index for it to match
            siblings = [path for path in child.iterdir() if path.name not in (".nav.yml", "index.md")]
            glob = "\n  - '*'" if siblings else ""
            (child / ".nav.yml").write_text(f"use_index_title: true\nnav:\n  - index.md{glob}\n")


if __name__ == "__main__":
    raise SystemExit(main())
