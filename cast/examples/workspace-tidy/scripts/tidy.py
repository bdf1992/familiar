from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SUFFIX = ".agentspells-disposable"


def tidy(workspace: Path) -> list[str]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError("workspace must be an existing directory")

    removed: list[str] = []
    for root, dirs, files in os.walk(workspace, followlinks=False):
        # Do not descend through symlinked directories.
        root_path = Path(root)
        dirs[:] = [name for name in dirs if not (root_path / name).is_symlink()]
        for name in files:
            if not name.endswith(SUFFIX):
                continue
            path = root_path / name
            # unlink removes the symlink itself if the marked file is a symlink.
            path.unlink()
            removed.append(path.relative_to(workspace).as_posix())

    return sorted(removed)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: tidy.py <workspace>", file=sys.stderr)
        return 2
    try:
        removed = tidy(Path(argv[1]))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"removed": removed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
